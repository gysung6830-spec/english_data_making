// 끌어다 놓으면 바로 올라갑니다. 무료 자료실과 상품 화면이 같이 씁니다.
(function () {
  var form = document.getElementById('dropForm');
  var zone = document.getElementById('dropZone');
  var input = document.getElementById('dropInput');
  var pick = document.getElementById('dropPick');
  if (!form || !zone || !input) return;
  var busy = zone.querySelector('.dz-busy');

  function send() {
    if (!input.files || !input.files.length) return;
    zone.classList.add('busy');
    if (busy) busy.hidden = false;
    form.submit();
  }

  if (pick) pick.addEventListener('click', function () { input.click(); });
  input.addEventListener('change', send);

  // 화면 어디에 놓아도 브라우저가 파일을 열어 버리지 않게 막습니다
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function (n) {
    document.addEventListener(n, function (e) { e.preventDefault(); });
  });
  ['dragenter', 'dragover'].forEach(function (n) {
    zone.addEventListener(n, function () { zone.classList.add('over'); });
  });
  ['dragleave', 'drop'].forEach(function (n) {
    zone.addEventListener(n, function () { zone.classList.remove('over'); });
  });
  zone.addEventListener('drop', function (e) {
    var files = e.dataTransfer && e.dataTransfer.files;
    if (!files || !files.length) return;
    var box = new DataTransfer();
    for (var i = 0; i < files.length; i++) box.items.add(files[i]);
    input.files = box.files;
    send();
  });
})();
