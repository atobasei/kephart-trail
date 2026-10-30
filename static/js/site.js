// Small progressive enhancements. Every page works without this file; it only adds
// conveniences on top of what the server already does.

// Forms marked with data-confirm ask before submitting (e.g. deleting a post).
for (const form of document.querySelectorAll("form[data-confirm]")) {
  form.addEventListener("submit", function (event) {
    if (!window.confirm(form.dataset.confirm)) {
      event.preventDefault();
    }
  });
}

// Every form with a password field gets one "Show password" checkbox that reveals
// all of that form's password fields while it's ticked.
for (const form of document.querySelectorAll("form")) {
  const fields = form.querySelectorAll('input[type="password"]');
  if (fields.length === 0) {
    continue;
  }

  const label = document.createElement("label");
  label.className = "show-password";
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  label.append(checkbox, " Show password");

  checkbox.addEventListener("change", function () {
    for (const field of fields) {
      if (checkbox.checked) {
        field.type = "text";
      } else {
        field.type = "password";
      }
    }
  });

  // Put it just below the last password field (after its wrapper, if it has one).
  const lastField = fields[fields.length - 1];
  let anchor = lastField;
  if (lastField.parentElement !== form) {
    anchor = lastField.parentElement;
  }
  anchor.after(label);
}
