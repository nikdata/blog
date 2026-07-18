(function () {
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function getCurrentTheme() {
    return localStorage.getItem("theme") || null;
  }

  toggle.addEventListener("click", function () {
    var current =
      document.documentElement.getAttribute("data-theme") || getSystemTheme();
    var next = current === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  });
})();
