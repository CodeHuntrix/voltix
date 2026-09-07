import { useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { api, authStore } from "@/lib/api";
import { colors } from "@/lib/tokens";

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@voltix.demo");
  const [password, setPassword] = useState("voltix-demo");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onLogin() {
    setBusy(true);
    setError(null);
    try {
      const tokens = await api.login(email, password);
      await authStore.setToken(tokens.access_token);
      const orgs = await api.orgs(tokens.access_token);
      const sites = await api.sites(tokens.access_token, orgs[0].id);
      await authStore.setSiteId(sites[0].id);
      router.replace("/home");
    } catch (e: any) {
      setError(String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.brand}>Voltix</Text>
      <Text style={styles.sub}>Floor / owner app · CT-estimated waste</Text>
      <TextInput
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        placeholder="Email"
        placeholderTextColor={colors.textMuted}
      />
      <TextInput
        style={styles.input}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        placeholder="Password"
        placeholderTextColor={colors.textMuted}
      />
      {error ? <Text style={styles.err}>{error}</Text> : null}
      <Pressable style={styles.btn} onPress={onLogin} disabled={busy}>
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Sign in</Text>}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, padding: 24, justifyContent: "center", backgroundColor: colors.surface },
  brand: { fontSize: 32, fontWeight: "700", color: colors.primary },
  sub: { color: colors.textMuted, marginBottom: 24, marginTop: 4 },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.elevated,
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    color: colors.text,
  },
  btn: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
    minHeight: 48,
  },
  btnText: { color: "#fff", fontWeight: "600" },
  err: { color: colors.danger, marginBottom: 8 },
});
