import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { useState } from "react";
import { Dialog } from "./Dialog";

describe("Dialog", () => {
  it("closes with Escape and returns focus to the trigger", async () => {
    const user = userEvent.setup();
    function DialogHost() {
      const [open, setOpen] = useState(false);
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>열기</button>
          <Dialog open={open} title="확인" description="설명" onClose={() => setOpen(false)}>
            <button type="button">확인</button>
          </Dialog>
        </>
      );
    }

    render(<DialogHost />);

    const trigger = screen.getByRole("button", { name: "열기" });
    await user.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "확인" });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toContainElement(document.activeElement as HTMLElement | null);

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "확인" })).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });
});
