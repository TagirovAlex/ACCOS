import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ErrorPage } from "../ErrorPage";

describe("ErrorPage", () => {
  it("renders status code and russian label", () => {
    render(<ErrorPage error={{ status: 404 }} />);
    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Ресурс не найден")).toBeInTheDocument();
  });

  it("renders error message in monospace block", () => {
    render(<ErrorPage error={{ status: 500, error: "Something broke" }} />);
    expect(screen.getByText("Something broke")).toBeInTheDocument();
  });

  it("renders chips for status, error_id, method, path", () => {
    render(
      <ErrorPage
        error={{
          status: 403,
          error_id: "err_abc123",
          request: { method: "POST", path: "/api/v1/chat/1/send" },
        }}
      />
    );
    expect(screen.getByText("HTTP 403")).toBeInTheDocument();
    expect(screen.getByText("ID: err_abc123")).toBeInTheDocument();
    expect(screen.getByText("POST")).toBeInTheDocument();
    expect(screen.getByText("/api/v1/chat/1/send")).toBeInTheDocument();
  });

  it("renders Назад and Обновить страницу buttons", () => {
    render(<ErrorPage error={{ status: 500 }} />);
    expect(screen.getByText("Назад")).toBeInTheDocument();
    expect(screen.getByText("Обновить страницу")).toBeInTheDocument();
  });

  it("renders Повторить button when onRetry is provided", () => {
    const onRetry = vi.fn();
    render(<ErrorPage error={{ status: 500 }} onRetry={onRetry} />);
    const btn = screen.getByText("Повторить");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
