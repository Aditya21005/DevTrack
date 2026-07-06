import { describe, expect, it } from "vitest";

import { authService } from "../api/auth.service";

describe("authService", () => {
  it("returns a mock session for valid login input", async () => {
    const session = await authService.login({ email: "avery@devtrack.ai", password: "devtrack-demo" });

    expect(session.accessToken).toBeTruthy();
    expect(session.user.email).toBe("avery@devtrack.ai");
    expect(session.user.role).toBe("owner");
  });
});