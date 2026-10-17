// LibraFlow - Client-Side JavaScript

document.addEventListener("DOMContentLoaded", function () {
  // Auto dismiss flash alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 5000);
  });

  // Demo credential quick-fill on login page
  const demoButtons = document.querySelectorAll(".btn-fill-demo");
  demoButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const usernameInput = document.getElementById("identifier");
      const passwordInput = document.getElementById("password");
      if (usernameInput && passwordInput) {
        usernameInput.value = this.getAttribute("data-user");
        passwordInput.value = this.getAttribute("data-pass");
        usernameInput.focus();
      }
    });
  });

  // Client-side quick filter for tables
  const tableSearchInput = document.getElementById("tableSearchInput");
  if (tableSearchInput) {
    tableSearchInput.addEventListener("keyup", function () {
      const filterValue = this.value.toLowerCase();
      const targetTable = document.querySelector(".filterable-table tbody");
      if (targetTable) {
        const rows = targetTable.getElementsByTagName("tr");
        for (let i = 0; i < rows.length; i++) {
          const text = rows[i].textContent.toLowerCase();
          rows[i].style.display = text.indexOf(filterValue) > -1 ? "" : "none";
        }
      }
    });
  }

  // Confirm delete or critical action dialogs
  const confirmForms = document.querySelectorAll("form.confirm-action");
  confirmForms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      const msg = form.getAttribute("data-confirm-message") || "Are you sure you want to perform this action?";
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
});
