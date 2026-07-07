document.addEventListener('DOMContentLoaded', function () {
  setTimeout(function () {
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  /* Smart Search */
  var searchInput = document.getElementById('smartSearchInput');
  var searchResults = document.getElementById('smartSearchResults');
  var searchForm = document.getElementById('smartSearchForm');
  var debounceTimer;

  if (searchInput && searchResults) {
    searchInput.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      var q = this.value.trim();
      if (q.length < 2) {
        searchResults.style.display = 'none';
        return;
      }
      debounceTimer = setTimeout(function () {
        fetch('/api/search/?q=' + encodeURIComponent(q))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            searchResults.innerHTML = '';
            if (data.results && data.results.length > 0) {
              data.results.forEach(function (p) {
                var a = document.createElement('a');
                a.className = 'dropdown-item d-flex align-items-center gap-2';
                a.href = '/products/' + p.slug + '/';
                var price = p.is_on_sale ? p.discount_price : p.price;
                a.innerHTML =
                  '<div style="flex:1;"><strong>' + p.name + '</strong><br><small class="text-muted">' +
                  p.category + ' — $' + price + '</small></div>';
                searchResults.appendChild(a);
              });
              searchResults.style.display = 'block';
            } else {
              searchResults.innerHTML = '<span class="dropdown-item text-muted">No results found</span>';
              searchResults.style.display = 'block';
            }
          })
          .catch(function () {
            searchResults.style.display = 'none';
          });
      }, 300);
    });

    document.addEventListener('click', function (e) {
      if (!searchForm.contains(e.target)) {
        searchResults.style.display = 'none';
      }
    });

    searchInput.addEventListener('focus', function () {
      if (searchResults.children.length > 0) {
        searchResults.style.display = 'block';
      }
    });
  }
});
