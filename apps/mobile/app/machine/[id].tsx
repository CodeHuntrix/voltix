import { useQuery } from "@tanstack/react-query";
import { useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { api, authStore } from "@/lib/api";
import { colors, stateColor } from "@/lib/tokens";

export default function MachineScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [token, setToken] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);
  useEffect(() => {
    (async () => {
      setToken(await authStore.getToken());
      setSiteId(await authStore.getSiteId());
    })();
  }, []);
  const live = useQuery({
    queryKey: ["live", siteId],
    enabled: !!token && !!siteId,
    queryFn: () => api.live(token!, siteId!),
    refetchInterval: 4000,
  });
  const m = (live.data ?? []).find((x) => x.machine_id === id);

  if (!m) {
    return (
      <View style={styles.wrap}>
        <Text style={{ color: colors.textMuted }}>Loading…</Text>
      </View>
    );
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.name}>{m.name}</Text>
      <View style={[styles.badge, { backgroundColor: stateColor(m.state) }]}>
        <Text style={styles.badgeText}>{m.state}</Text>
      </View>
      <Text style={styles.kw}>{m.kw_est.toFixed(2)} kW · {m.i_rms_a.toFixed(1)} A</Text>
      <Text style={styles.meta}>
        Waste ₹{m.waste_inr_per_hr.toFixed(0)}/hr · model {m.model_version}
      </Text>
      <Text style={styles.note}>CT-only estimate — not billing-grade.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, padding: 16, backgroundColor: colors.surface },
  name: { fontSize: 22, fontWeight: "700", color: colors.text },
  badge: {
    alignSelf: "flex-start",
    marginTop: 12,
    borderRadius: 4,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeText: { color: "#fff", fontWeight: "700", fontSize: 12 },
  kw: { marginTop: 16, fontSize: 18, color: colors.text },
  meta: { marginTop: 8, color: colors.textMuted },
  note: { marginTop: 24, color: colors.textMuted, fontSize: 12 },
});
