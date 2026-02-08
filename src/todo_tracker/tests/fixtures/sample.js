// Sample JavaScript file for testing TODO extraction.

function main() {
  // TODO: add input validation
  const data = fetchData();

  // FIXME: XSS vulnerability in user input rendering
  document.innerHTML = data.html;

  /* HACK: setTimeout to wait for DOM update
     This should use MutationObserver instead */
  setTimeout(() => render(data), 100);
}

function fetchData() {
  // TODO(jsmith): switch to fetch API
  return {};
}
