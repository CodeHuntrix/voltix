import { useQuery } from "@tanstack/react-query";
import { Link, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { api, authStore } from "@/lib/api";
import { colors, stateColor } from "@/lib/tokens";

export default function HomeScreen() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const t = await authStore.getToken();
      const s = await authStore.getSiteId();
      if (!t || !s) {
        router.replace("/");
        return;
      }
      setToken(t);
      setSiteId(s);
    })();
  }, []);

  const live = useQuery({
    queryKey: ["live", siteId],
    enabled: !!token && !!siteId,
    queryFn: () => api.live(token!, siteId!),
    refetchInterval: 4000,
  });

  return (
    <View style={styles.wrap}>
      <View style={styles.nav}>
        <Link href="/rank" style={styles.link}>
          Rank
        </Link>
        <Link href="/alerts" style={styles.link}>
          Alerts
        </Link>
        <Link href="/autocut" style={styles.link}>
          AutoCut
        </Link>
        <Link href="/profile" style={styles.link}>
          Profile
        </Link>
      </View>
      <FlatList
        data={live.data ?? []}
        keyExtractor={(item) => item.machine_id}
        contentContainerStyle={{ padding: 16, gap: 10 }}
        ListEmptyComponent={
          <Text style={{ color: colors.textMuted }}>
            {live.isLoading ? "Loading…" : "No machines"}
          </Text>
        }
        renderItem={({ item }) => (
          <Pressable
            style={styles.card}
            onPress={() => router.push(`/machine/${item.machine_id}`)}
          >
            <View style={styles.row}>
              <Text style={styles.name}>{item.name}</Text>
              <View style={[styles.badge, { backgroundColor: stateColor(item.state) }]}>
                <Text style={styles.badgeText}>{item.state}</Text>
              </View>
            </View>
            <Text style={styles.kw}>{item.kw_est.toFixed(2)} kW</Text>
            {item.state === "WASTE" ? (
              <Text style={styles.waste}>₹{item.waste_inr_per_hr.toFixed(0)}/hr waste</Text>
            ) : (
              <Text style={styles.meta}>{item.i_rms_a.toFixed(1)} A · CT est.</Text>
            )}
          </Pressable>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: colors.surface },
  nav: {
    flexDirection: "row",
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.elevated,
  },
  link: { color: colors.primary, fontWeight: "600" },
  card: {
    backgroundColor: colors.elevated,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
  },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  name: { fontWeight: "600", color: colors.text, flex: 1, marginRight: 8 },
  badge: { borderRadius: 4, paddingHorizontal: 8, paddingVertical: 3 },
  badgeText: { color: "#fff", fontSize: 10, fontWeight: "700" },
  kw: { marginTop: 10, fontSize: 20, fontVariant: ["tabular-nums"], color: colors.text },
  waste: { marginTop: 4, color: colors.danger },
  meta: { marginTop: 4, color: colors.textMuted, fontSize: 12 },
});
