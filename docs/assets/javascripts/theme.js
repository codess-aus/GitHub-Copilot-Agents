(() => {
  const syncTheme = () => {
    const scheme = document.body.getAttribute("data-md-color-scheme");
    document.documentElement.setAttribute("data-theme", scheme === "slate" ? "dark" : "light");
  };
  new MutationObserver(syncTheme).observe(document.body, {
    attributes: true,
    attributeFilter: ["data-md-color-scheme"],
  });
  syncTheme();
})();
