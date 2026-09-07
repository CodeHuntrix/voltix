import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { api, authStore } from "@/lib/api";
import { colors } from "@/lib/tokens";

export default function AlertsScreen() {
  const [token, setToken] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);
  useEffect(() => {
    (async () => {
      setToken(await authStore.getToken());
      setSiteId(await authStore.getSiteId());
    })();
  }, []);
  const alerts = useQuery({
    queryKey: ["alerts", siteId],
    enabled: !!token && !!siteId,
    queryFn: () => api.alerts(token!, siteId!),
    refetchInterval: 5000,
  });

  return (
    <FlatList
      style={{ backgroundColor: colors.surface }}
      contentContainerStyle={{ padding: 16, gap: 10 }}
      data={alerts.data ?? []}
      keyExtractor={(i) => i.id}
      ListEmptyComponent={<Text style={{ color: colors.textMuted }}>Inbox empty</Text>}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.msg}>{item.message}</Text>
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
  title: { fontWeight: "600", color: colors.text },
  msg: { marginTop: 4, color: colors.textMuted, fontSize: 13 },
});
