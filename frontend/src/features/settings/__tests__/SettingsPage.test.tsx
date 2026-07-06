import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { renderWithProviders } from "@/test/renderWithProviders";
import { useUiStore } from "@/store/ui.store";
import SettingsPage from "../pages/SettingsPage";

describe("SettingsPage", () => {
  beforeEach(() => {
    useUiStore.setState({ theme: "light", sidebarOpen: true });
    document.documentElement.classList.remove("dark");
  });

  it("renders workspace settings and member management", async () => {
    renderWithProviders(<SettingsPage />);

    expect(await screen.findByText("Workspace Defaults")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Members" })).toBeInTheDocument();
    expect(screen.getByText("Invite Member")).toBeInTheDocument();
  });

  it("toggles dark theme through Zustand state", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);

    await screen.findByText("Theme");
    await user.click(screen.getByRole("button", { name: /dark/i }));

    await waitFor(() => expect(useUiStore.getState().theme).toBe("dark"));
  });
});
