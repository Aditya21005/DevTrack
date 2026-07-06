import { Suspense } from "react";
import { RouterProvider } from "react-router-dom";

import { AppProviders } from "./providers/AppProviders";
import { router } from "./router/router";

export function App() {
  return (
    <AppProviders>
      <Suspense fallback={<div className="p-6 text-sm text-foreground/70">Loading DevTrack AI...</div>}>
        <RouterProvider router={router} />
      </Suspense>
    </AppProviders>
  );
}
