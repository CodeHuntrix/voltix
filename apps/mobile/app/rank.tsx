import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { api, authStore } from "@/lib/api";
import { colors } from "@/lib/tokens";

export default function RankScreen() {
  const [token, setToken] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);
  useEffect(() => {
    (async () => {
      setToken(await authStore.getToken());
      setSiteId(await authStore.getSiteId());
    })();
  }, []);
  const rank = useQuery({
    queryKey: ["rank", siteId],
    enabled: !!token && !!siteId,
    queryFn: () => api.rank(token!, siteId!),
    refetchInterval: 5000,
  });

  return (
    <FlatList
      style={{ backgroundColor: colors.surface }}
      contentContainerStyle={{ padding: 16, gap: 10 }}
      data={rank.data ?? []}
      keyExtractor={(i) => i.machine_id}
      ListEmptyComponent={<Text style={{ color: colors.textMuted }}>No ranked waste yet</Text>}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.name}>{item.name}</Text>
          <Text style={styles.line}>
            {item.state} · {item.duration_min}m · ₹{item.waste_inr} · score {item.score}
          </Text>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.elevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 14,
  },
  name: { fontWeight: "600", color: colors.text },
  line: { marginTop: 6, color: colors.textMuted, fontSize: 13 },
});
