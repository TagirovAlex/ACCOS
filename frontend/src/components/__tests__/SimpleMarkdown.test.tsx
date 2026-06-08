import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SimpleMarkdown } from "../SimpleMarkdown";

describe("SimpleMarkdown", () => {
  it("renders plain text", () => {
    render(<SimpleMarkdown text="hello world" />);
    expect(screen.getByText("hello world")).toBeInTheDocument();
  });

  it("renders bold text", () => {
    render(<SimpleMarkdown text="this is **bold** text" />);
    const el = screen.getByText("bold");
    expect(el.tagName).toBe("STRONG");
  });

  it("renders italic text", () => {
    render(<SimpleMarkdown text="this is *italic* text" />);
    const el = screen.getByText("italic");
    expect(el.tagName).toBe("EM");
  });

  it("renders inline code", () => {
    render(<SimpleMarkdown text="use `code` here" />);
    const el = screen.getByText("code");
    expect(el.tagName).toBe("CODE");
  });

  it("renders code block", () => {
    render(<SimpleMarkdown text={"```python\nprint('hi')\n```"} />);
    const el = screen.getByText("print('hi')");
    expect(el.tagName).toBe("CODE");
  });

  it("escapes HTML in text", () => {
    render(<SimpleMarkdown text={"<script>alert('xss')</script>"} />);
    const el = screen.getByText("<script>alert('xss')</script>");
    expect(el).toBeInTheDocument();
  });
});
