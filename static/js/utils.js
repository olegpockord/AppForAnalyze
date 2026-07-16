  // code for open modal window for id choose
  function isAmbiguousId(value) {
    return /^\d{6,16}$/.test(value);
  }

  const form = document.querySelector('form[role="search"]');
  const input = form.querySelector('input[name="q"]');

  const modalEl = document.getElementById('idChoiceModal');
  const modal = new bootstrap.Modal(modalEl);

  let pendingValue = null;

  form.addEventListener('submit', function (e) {
    const value = input.value.trim();

    if (!isAmbiguousId(value)) {
      return;
    }

    e.preventDefault();
    pendingValue = value;
    modal.show();
  });

  document.getElementById('pmidBtn').addEventListener('click', () => {
    input.value = `pmid${pendingValue}`;
    modal.hide();
    form.submit();
  });

  document.getElementById('magBtn').addEventListener('click', () => {
    input.value = `mag${pendingValue}`;
    modal.hide();
    form.submit();
  });
// message window dissepear
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alertEl => {
        alertEl.addEventListener('closed.bs.alert', () => {
            alertEl.closest('.alert-wrapper').remove();
        });

        bootstrap.Alert.getOrCreateInstance(alertEl).close();
    });
  }, 5000);
  
