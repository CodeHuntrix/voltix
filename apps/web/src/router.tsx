import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
  redirect,
} from "@tanstack/react-router";
import { useAuth } from "@/lib/auth";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { MachinePage } from "@/pages/MachinePage";
import { AlertsPage } from "@/pages/AlertsPage";
import { AutocutPage } from "@/pages/AutocutPage";
import { MvPage } from "@/pages/MvPage";
import { AdminPage } from "@/pages/AdminPage";

function requireAuth() {
  const { accessToken, siteId } = useAuth.getState();
  if (!accessToken || !siteId) {
    throw redirect({ to: "/login" });
  }
}

const rootRoute = createRootRoute({
  component: () => <Outlet />,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

const onboardingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/onboarding",
  beforeLoad: requireAuth,
  component: OnboardingPage,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: LandingPage,
});

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/dashboard",
  beforeLoad: requireAuth,
  component: DashboardPage,
});

const machineRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/machines/$machineId",
  beforeLoad: requireAuth,
  component: MachinePage,
});

const alertsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/alerts",
  beforeLoad: requireAuth,
  component: AlertsPage,
});

const autocutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/autocut",
  beforeLoad: requireAuth,
  component: AutocutPage,
});

const mvRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/mv",
  beforeLoad: requireAuth,
  component: MvPage,
});

const adminRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/admin",
  beforeLoad: requireAuth,
  component: AdminPage,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  onboardingRoute,
  dashboardRoute,
  machineRoute,
  alertsRoute,
  autocutRoute,
  mvRoute,
  adminRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
