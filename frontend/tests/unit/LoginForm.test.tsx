import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

const apiFetchMock = vi.fn();
vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>(
    "@/lib/api-client"
  );
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => apiFetchMock(...args),
  };
});

const setTokensMock = vi.fn();
vi.mock("@/lib/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/auth")>("@/lib/auth");
  return {
    ...actual,
    setTokens: (...args: unknown[]) => setTokensMock(...args),
  };
});

import { LoginForm } from "@/components/forms/LoginForm";
import { ApiError } from "@/lib/api-client";

describe("LoginForm", () => {
  beforeEach(() => {
    pushMock.mockClear();
    apiFetchMock.mockReset();
    setTokensMock.mockClear();
  });

  it("blocks submit and shows field errors for empty/invalid input, without calling the API", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/enter a valid email address/i)).toBeInTheDocument();
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
    expect(apiFetchMock).not.toHaveBeenCalled();
  });

  it("logs in successfully: stores tokens and redirects to /dashboard", async () => {
    apiFetchMock.mockResolvedValueOnce({
      access_token: "access-123",
      refresh_token: "refresh-456",
      token_type: "bearer",
    });

    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "owner@finpilot.demo");
    await user.type(screen.getByLabelText(/password/i), "correct-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(setTokensMock).toHaveBeenCalledWith("access-123", "refresh-456");
    });
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
  });

  it("shows the server error message and does not redirect on invalid credentials", async () => {
    apiFetchMock.mockRejectedValueOnce(new ApiError(401, "Invalid email or password"));

    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "owner@finpilot.demo");
    await user.type(screen.getByLabelText(/password/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid email or password/i);
    expect(pushMock).not.toHaveBeenCalled();
    expect(setTokensMock).not.toHaveBeenCalled();
  });
});
