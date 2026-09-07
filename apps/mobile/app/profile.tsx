import { useQuery } from "@tanstack/react-query";
import * as Notifications from "expo-notifications";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { api, authStore } from "@/lib/api";
import { colors } from "@/lib/tokens";

export default function ProfileScreen() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);
  const [pushNote, setPushNote] = useState("not registered");

  useEffect(() => {
    (async () => {
      setToken(await authStore.getToken());
      setSiteId(await authStore.getSiteId());
    })();
  }, []);

  const reports = useQuery({
    queryKey: ["mv", siteId],
    enabled: !!token && !!siteId,
    queryFn: () => api.mvReports(token!, siteId!),
  });

  async function registerPush() {
    if (!token) return;
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== "granted") {
      setPushNote("permission denied");
      return;
    }
    const expoToken = (await Notifications.getExpoPushTokenAsync()).data;
    await api.pushToken(token, expoToken);
    setPushNote(`registered ${expoToken.slice(0, 18)}…`);
  }

  async function logout() {
    await authStore.clear();
    router.replace("/");
  }

  const latest = reports.data?.[0];

  return (
    <View style={styles.wrap}>
      <Text style={styles.h}>Site</Text>
      <Text style={styles.mono}>{siteId}</Text>
      <Text style={[styles.h, { marginTop: 20 }]}>M&V summary</Text>
      {latest ? (
        <Text style={styles.body}>
          Savings {latest.savings_kwh.toFixed(1)} kWh · ₹{latest.savings_inr.toFixed(0)}
        </Text>
      ) : (
        <Text style={styles.body}>No reports yet — generate from web console.</Text>
      )}
      <Pressable style={styles.btn} onPress={registerPush}>
        <Text style={styles.btnText}>Enable Expo push hooks</Text>
      </Pressable>
      <Text style={styles.meta}>{pushNote}</Text>
      <Pressable style={[styles.btn, styles.out]} onPress={logout}>
        <Text style={[styles.btnText, { color: colors.danger }]}>Sign out</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, padding: 16, backgroundColor: colors.surface },
  h: { fontWeight: "700", color: colors.textMuted, fontSize: 12, textTransform: "uppercase" },
  mono: { marginTop: 6, color: colors.text, fontFamily: "monospace" },
  body: { marginTop: 8, color: colors.text },
  btn: {
    marginTop: 24,
    backgroundColor: colors.primary,
    padding: 14,
    borderRadius: 8,
    alignItems: "center",
    minHeight: 48,
  },
  out: { backgroundColor: colors.elevated, borderWidth: 1, borderColor: colors.border },
  btnText: { color: "#fff", fontWeight: "600" },
  meta: { marginTop: 8, color: colors.textMuted, fontSize: 12 },
});
