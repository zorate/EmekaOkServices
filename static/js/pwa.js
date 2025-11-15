if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker
      .register("/static/js/service-worker.js")
      .then(() => console.log("Service Worker registered"))
      .catch(err => console.log("SW registration failed: ", err));
  });
}
