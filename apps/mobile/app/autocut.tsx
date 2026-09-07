import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { api, authStore } from "@/lib/api";
import { colors } from "@/lib/tokens";

export default function AutocutScreen() {
  const [token, setToken] = useState<string | null>(null);
  const [siteId, setSiteId] = useState<string | null>(null);
  const qc = useQueryClient();
  useEffect(() => {
    (async () => {
      setToken(await authStore.getToken());
      setSiteId(await authStore.getSiteId());
    })();
  }, []);
  const cmds = useQuery({
    queryKey: ["autocut", siteId],
    enabled: !!token && !!siteId,
    queryFn: () => api.autocutList(token!, siteId!),
    refetchInterval: 4000,
  });
  const decide = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) =>
      api.autocutDecide(token!, id, approve),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["autocut", siteId] }),
  });

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface }}>
      <Text style={styles.warn}>Eligible loads only (≤10A relay).</Text>
      <FlatList
        contentContainerStyle={{ padding: 16, gap: 10 }}
        data={cmds.data ?? []}
        keyExtractor={(i) => i.id}
        ListEmptyComponent={<Text style={{ color: colors.textMuted }}>No commands</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.status}>{item.status}</Text>
            <Text style={styles.reason}>{item.reason}</Text>
            {item.status === "pending" ? (
              <View style={styles.row}>
                <Pressable
                  style={[styles.btn, { backgroundColor: colors.success }]}
                  onPress={() => decide.mutate({ id: item.id, approve: true })}
                >
                  <Text style={styles.btnText}>Approve</Text>
                </Pressable>
                <Pressable
                  style={[styles.btn, { backgroundColor: colors.danger }]}
                  onPress={() => decide.mutate({ id: item.id, approve: false })}
                >
                  <Text style={styles.btnText}>Deny</Text>
                </Pressable>
              </View>
            ) : null}
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  warn: { padding: 12, color: colors.warning, backgroundColor: colors.muted, fontSize: 12 },
  card: {
    backgroundColor: colors.elevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 14,
  },
  status: { fontWeight: "700", color: colors.text, textTransform: "uppercase", fontSize: 12 },
  reason: { marginTop: 6, color: colors.textMuted },
  row: { flexDirection: "row", gap: 8, marginTop: 12 },
  btn: { flex: 1, padding: 12, borderRadius: 8, alignItems: "center", minHeight: 44 },
  btnText: { color: "#fff", fontWeight: "600" },
});
