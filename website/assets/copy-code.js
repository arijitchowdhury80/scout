(() => {
  function copyWithFallback(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "readonly");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    return copied ? Promise.resolve() : Promise.reject(new Error("Copy failed"));
  }

  function enhanceCodeBlocks() {
    document.querySelectorAll("pre > code").forEach((code, index) => {
      const pre = code.parentElement;
      if (!pre || pre.parentElement?.classList.contains("code-copy")) {
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "code-copy";
      pre.parentNode?.insertBefore(wrapper, pre);
      wrapper.appendChild(pre);

      const button = document.createElement("button");
      button.type = "button";
      button.className = "code-copy__button";
      button.textContent = "Copy";
      button.setAttribute("aria-label", `Copy code sample ${index + 1}`);
      wrapper.appendChild(button);

      button.addEventListener("click", async () => {
        const original = button.textContent;
        button.disabled = true;
        try {
          await copyWithFallback(code.textContent || "");
          button.textContent = "Copied";
          button.dataset.state = "success";
        } catch {
          button.textContent = "Copy failed";
          button.dataset.state = "error";
        } finally {
          window.setTimeout(() => {
            button.textContent = original;
            button.disabled = false;
            delete button.dataset.state;
          }, 1800);
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhanceCodeBlocks);
  } else {
    enhanceCodeBlocks();
  }
})();
