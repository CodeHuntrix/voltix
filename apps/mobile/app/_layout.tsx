import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import { colors } from "@/lib/tokens";

export default function RootLayout() {
  const [qc] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={qc}>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.elevated },
          headerTintColor: colors.primary,
          headerTitleStyle: { fontWeight: "600" },
          contentStyle: { backgroundColor: colors.surface },
        }}
      >
        <Stack.Screen name="index" options={{ title: "Voltix" }} />
        <Stack.Screen name="home" options={{ title: "Live" }} />
        <Stack.Screen name="rank" options={{ title: "Ranked waste" }} />
        <Stack.Screen name="machine/[id]" options={{ title: "Machine" }} />
        <Stack.Screen name="alerts" options={{ title: "Alerts" }} />
        <Stack.Screen name="autocut" options={{ title: "AutoCut" }} />
        <Stack.Screen name="profile" options={{ title: "Profile" }} />
      </Stack>
    </QueryClientProvider>
  );
}
