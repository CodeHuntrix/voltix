"""
Voltix Pulse Engine - Continuous Current Sensor & Waste Detection Test
Simulates continuous telemetry from a machine CT sensor and validates the
Pulse Engine's temporal duration-based WASTE detection policy.

Relationship between GMM and WASTE:
  - The Gaussian Mixture Model (GMM) classifies the machine's INSTANTANEOUS electrical
    operating state (OFF, IDLE, ACTIVE) based on current and short-term rolling statistics.
  - An unloaded machine (e.g. air compressor motor spinning without compression) draws ~3.8 A
    whether idling briefly during a normal operational cycle or wasting power for hours.
  - Therefore, WASTE is NOT a separate instantaneous GMM cluster. It is a temporal policy
    state evaluated by the Pulse Engine: sustained IDLE for >= threshold (default 300s) = WASTE.
"""

import os
import sys
import time
import random
import argparse
from datetime import datetime

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pulse.predict import (
    predict_pulse_state,
    reset_machine_state,
    load_model_and_meta
)
from src.pulse.model_registry import resolve_machine_id, get_machine_config

# Default simulated operating phases (state, duration_in_seconds)
# The final 360-second IDLE phase tests the 300-second WASTE threshold
DEFAULT_PHASES = [
    ("OFF", 20),
    ("IDLE", 60),
    ("ACTIVE", 30),
    ("IDLE", 360)
]


def generate_simulated_current(simulated_state: str) -> float:
    """
    Generate realistic random RMS current (Amperes) according to operating state.
    OFF:            0.00 - 0.10 A  (motor stopped/unpowered)
    IDLE/unloaded:  3.50 - 4.20 A  (motor spinning without compression)
    ACTIVE/loaded:  5.50 - 6.50 A  (active compression pumping air)
    """
    if simulated_state == "OFF":
        val = random.gauss(0.038, 0.005)
        return round(float(min(max(val, 0.01), 0.08)), 4)
    elif simulated_state == "IDLE":
        val = random.gauss(3.82, 0.05)
        return round(float(min(max(val, 3.55), 4.15)), 4)
    elif simulated_state == "ACTIVE":
        val = random.gauss(6.05, 0.12)
        return round(float(min(max(val, 5.60), 6.45)), 4)
    else:
        return 0.0


def run_continuous_test(
    machine_id: str = "compressor_01",
    sensing_interval: float = 1.0,
    phases: list[tuple[str, float]] | None = None,
    max_samples: int | None = None
) -> None:
    """
    Runs the continuous simulated sensor loop.
    """
    m_id = resolve_machine_id(machine_id)
    config = get_machine_config(m_id)
    waste_config = config.get("waste_detection", {})
    waste_threshold = waste_config.get("duration_seconds", 300)
    
    phases_to_run = phases if phases is not None else DEFAULT_PHASES
    
    # Load model and metadata to verify availability
    _, meta = load_model_and_meta(m_id)
    model_version = meta.get("model_version", "gmm-v1")
    
    # Reset temporal state tracker at startup
    reset_machine_state(m_id)
    
    print("\n" + "=" * 60)
    print("VOLTIX PULSE ENGINE - CONTINUOUS SENSOR TEST")
    print("=" * 60)
    print(f"Machine           : {m_id}")
    print(f"Model Version     : {model_version}")
    print(f"Sampling interval : {sensing_interval:.2f} sec")
    print(f"WASTE threshold   : {waste_threshold} sec")
    print("Simulated schedule:")
    for idx, (p_name, p_dur) in enumerate(phases_to_run):
        print(f"  Phase {idx + 1}: {p_name:6s} for {p_dur} sec")
    print("Press Ctrl+C at any time to stop and view validation summary.")
    print("=" * 60 + "\n")
    
    # History buffer for causal feature calculation
    history: list[float] = []
    
    # Test-side idle observability timer
    idle_start_time_mono: float | None = None
    idle_start_time_dt: str | None = None
    idle_duration_sec: float = 0.0
    
    # Summary statistics
    total_samples = 0
    state_counts = {"OFF": 0, "IDLE": 0, "ACTIVE": 0, "WASTE": 0}
    first_waste_dt: str | None = None
    max_idle_duration: float = 0.0
    
    start_mono = time.monotonic()
    next_sample_mono = start_mono
    
    phase_idx = 0
    phase_elapsed = 0.0
    
    try:
        while True:
            # Drift-free timing: sleep only until the next scheduled tick
            now_mono = time.monotonic()
            sleep_duration = next_sample_mono - now_mono
            if sleep_duration > 0:
                time.sleep(sleep_duration)
                
            now_dt = datetime.now()
            sample_ts_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine current simulated phase
            current_phase_name, current_phase_duration = phases_to_run[phase_idx]
            
            # Generate simulated current reading
            i_rms_a = generate_simulated_current(current_phase_name)
            
            # Call existing Voltix Pulse Engine inference API
            pulse_state, confidence, _ = predict_pulse_state(
                machine_id=m_id,
                i_rms_a=i_rms_a,
                history_i=history,
                time_delta_seconds=sensing_interval
            )
            
            # Update history buffer (keep last 5 readings for 3-sample causal window)
            history.append(i_rms_a)
            if len(history) > 5:
                history.pop(0)
                
            # Instantaneous GMM state vs Pulse Engine final state:
            # The GMM classifies the instantaneous electrical operating pattern (OFF, IDLE, ACTIVE).
            # When prolonged IDLE is detected by the Pulse Engine, final state transitions to WASTE.
            instantaneous_gmm_state = "IDLE" if pulse_state == "WASTE" else pulse_state
            
            # Test-side idle duration tracking
            if instantaneous_gmm_state == "IDLE":
                if idle_start_time_mono is None:
                    idle_start_time_mono = time.monotonic()
                    idle_start_time_dt = sample_ts_str
                idle_duration_sec = time.monotonic() - idle_start_time_mono
            else:
                idle_start_time_mono = None
                idle_start_time_dt = None
                idle_duration_sec = 0.0
                
            if idle_duration_sec > max_idle_duration:
                max_idle_duration = idle_duration_sec
                
            # Record summary counts
            total_samples += 1
            state_counts[pulse_state] = state_counts.get(pulse_state, 0) + 1
            if pulse_state == "WASTE" and first_waste_dt is None:
                first_waste_dt = sample_ts_str
                
            # Terminal display
            if pulse_state == "WASTE":
                print("------------------------------------------------------------")
                print(">>> WASTE DETECTED <<<")
                print(f"Timestamp       : {sample_ts_str}")
                print(f"Simulated Phase : {current_phase_name}")
                print(f"Current         : {i_rms_a:.2f} A")
                print(f"GMM State       : {instantaneous_gmm_state}")
                print(f"Pulse State     : {pulse_state}")
                print(f"Confidence      : {confidence:.4f}")
                print(f"Model Version   : {model_version}")
                print(f"Idle Started    : {idle_start_time_dt}")
                print(f"Idle Duration   : {idle_duration_sec:.1f} sec")
                print("------------------------------------------------------------")
            else:
                idle_start_display = idle_start_time_dt if idle_start_time_dt else "N/A"
                print("------------------------------------------------------------")
                print(f"Timestamp       : {sample_ts_str}")
                print(f"Simulated Phase : {current_phase_name}")
                print(f"Current         : {i_rms_a:.2f} A")
                print(f"GMM State       : {instantaneous_gmm_state}")
                print(f"Pulse State     : {pulse_state}")
                print(f"Confidence      : {confidence:.4f}")
                print(f"Model Version   : {model_version}")
                print(f"Idle Started    : {idle_start_display}")
                print(f"Idle Duration   : {idle_duration_sec:.1f} sec")
                print("------------------------------------------------------------")
                
            # Advance phase scheduler
            phase_elapsed += sensing_interval
            if phase_elapsed >= current_phase_duration:
                phase_elapsed = 0.0
                phase_idx = (phase_idx + 1) % len(phases_to_run)
                next_phase_name, next_phase_dur = phases_to_run[phase_idx]
                print(f"\n>>> TRANSITION: Entering phase '{next_phase_name}' for {next_phase_dur}s <<<\n")
                
            # Schedule next tick (drift-free)
            next_sample_mono += sensing_interval
            if next_sample_mono < time.monotonic():
                next_sample_mono = time.monotonic()
                
            if max_samples and total_samples >= max_samples:
                print("\nReached max_samples limit.")
                break
                
    except KeyboardInterrupt:
        print("\n\nTest stopped.")
    finally:
        # Reset state on shutdown
        reset_machine_state(m_id)
        
    # Print validation summary
    total_elapsed = time.monotonic() - start_mono
    waste_passed = state_counts.get("WASTE", 0) > 0
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total samples        : {total_samples}")
    print(f"Total elapsed time   : {total_elapsed:.1f} sec")
    print(f"OFF predictions      : {state_counts.get('OFF', 0)}")
    print(f"IDLE predictions     : {state_counts.get('IDLE', 0)}")
    print(f"ACTIVE predictions   : {state_counts.get('ACTIVE', 0)}")
    print(f"WASTE predictions    : {state_counts.get('WASTE', 0)}")
    print(f"First WASTE detected : {first_waste_dt if first_waste_dt else 'None'}")
    print(f"Max idle duration    : {max_idle_duration:.1f} sec")
    print("-" * 60)
    if waste_passed:
        print("WASTE TEST: PASSED (Prolonged IDLE successfully transitioned to WASTE)")
    else:
        print("WASTE TEST: NOT TRIGGERED (Test stopped before threshold was reached)")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Voltix Pulse Engine Continuous Current Sensor Test")
    parser.add_argument("--machine", default="compressor_01", help="Machine ID (default: compressor_01)")
    parser.add_argument("--interval", type=float, default=None, help="Sensing interval in seconds")
    parser.add_argument("--fast", action="store_true", help="Accelerated test mode with scaled phase durations")
    parser.add_argument("--max-samples", type=int, default=None, help="Stop automatically after N samples")
    
    args = parser.parse_args()
    
    # Prompt for sensing interval if not provided via CLI
    if args.interval is not None:
        sensing_interval = args.interval
    else:
        try:
            user_input = input("Enter sensing interval in seconds [default 1]: ").strip()
            if not user_input:
                sensing_interval = 1.0
            else:
                sensing_interval = float(user_input)
                if sensing_interval <= 0:
                    print("Invalid interval. Defaulting to 1.0 second.")
                    sensing_interval = 1.0
        except (EOFError, KeyboardInterrupt):
            sensing_interval = 1.0
            print()
            
    # Phase schedule
    if args.fast:
        phases = [
            ("OFF", 4),
            ("IDLE", 6),
            ("ACTIVE", 4),
            ("IDLE", 320)
        ]
    else:
        phases = DEFAULT_PHASES
        
    run_continuous_test(
        machine_id=args.machine,
        sensing_interval=sensing_interval,
        phases=phases,
        max_samples=args.max_samples
    )


if __name__ == "__main__":
    main()
