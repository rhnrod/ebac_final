document.addEventListener("DOMContentLoaded", function () {
  function detectOS() {
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();
    return platform.includes('mac') || userAgent.includes('mac');
  }

  const isMac = detectOS();

  if (window.innerWidth < 1280) return 

  if (isMac) {
    document.getElementById("macOnly").classList.remove("hidden");
    document.getElementById("notMac").classList.add("hidden");
  } else {
    document.getElementById("macOnly").classList.add("hidden");
    document.getElementById("notMac").classList.remove("hidden");
  }

  // Atalho Ctrl+Shift+K (Windows/Linux) ou Command+Shift+K (macOS)
  document.addEventListener('keydown', function (e) {
    const isShortcut = isMac
      ? e.metaKey && e.shiftKey && e.key.toLowerCase() === 'k'   // Command+Shift+K
      : e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'k'; // Ctrl+Shift+K

    if (isShortcut) {
      const inputBusca = document.querySelector('input[type="search"]');
      if (inputBusca) {
        inputBusca.focus();
        e.preventDefault(); // Evita comportamento inesperado
      }
    }
  });
});