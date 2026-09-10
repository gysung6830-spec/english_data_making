/* 단어 게임 셋. 문제를 푼다는 느낌이 안 나야 한 번 더 하게 됩니다.
   기록은 이 브라우저에만 두고, 아무 데도 보내지 않습니다. */
(function () {
  var board = document.getElementById('board');
  if (!board) return;
  var EN = JSON.parse(document.getElementById('gameWords').textContent);
  var KO = JSON.parse(document.getElementById('gameMeans').textContent);
  var kind = board.dataset.game;
  var best = parseInt(board.dataset.best, 10) || 10;

  var A = document.getElementById('gA'), AL = document.getElementById('gAL');
  var B = document.getElementById('gB'), BL = document.getElementById('gBL');
  var C = document.getElementById('gC'), CL = document.getElementById('gCL');
  var done = document.getElementById('done');
  var doneHead = document.getElementById('doneHead');
  var doneBody = document.getElementById('doneBody');

  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function keep(name, value, bigger) {
    var key = 'ortica-game-' + kind + '-' + name;
    var had = null;
    try { had = localStorage.getItem(key); } catch (e) { return null; }
    var was = had == null ? null : +had;
    var better = was == null || (bigger ? value > was : value < was);
    if (better) { try { localStorage.setItem(key, String(value)); } catch (e) {} }
    return { was: was, better: better };
  }
  function finish(head, body, stats) {
    done.hidden = false;
    doneHead.textContent = head;
    doneBody.textContent = body;
    card(head, stats);
    done.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  /* 다 하고 나서 그림 한 장. 저장하거나 그대로 보내실 수 있습니다. */
  function card(head, stats) {
    var box = document.getElementById('gameCard');
    if (!box || !window.OrticaCard) return;
    box.dataset.made = '';                    // 다시 하면 새 기록으로 다시 그립니다
    var info = {};
    try { info = JSON.parse(document.getElementById('gameInfo').textContent); }
    catch (e) { /* 없어도 카드는 그립니다 */ }
    OrticaCard.attach(box, {
      brand: info.brand, site: info.site, kind: info.kind,
      title: info.title, scope: info.scope,
      big: String(head).split('·').pop().trim() || head,
      say: info.kind + ' 기록',
      stats: stats || []
    });
  }

  /* ── 짝 맞추기 ─────────────────────────────────────────────────── */
  function match() {
    AL.textContent = '뒤집은 횟수'; BL.textContent = '남은 짝'; CL.textContent = '맞힌 짝';
    var pairs = Math.min(8, EN.length);
    var pick = shuffle(EN.map(function (w, i) { return i; })).slice(0, pairs);
    var cards = shuffle(pick.map(function (i) { return { i: i, side: 'en' }; })
      .concat(pick.map(function (i) { return { i: i, side: 'ko' }; })));

    var flips = 0, found = 0, open = [], lock = false;
    A.textContent = '0'; B.textContent = String(pairs); C.textContent = '0';
    board.className = 'g-board g-match';
    board.innerHTML = '';

    cards.forEach(function (c) {
      var node = el('button', 'mc');
      node.type = 'button';
      node.appendChild(el('span', 'mc-face', c.side === 'en' ? EN[c.i] : KO[c.i]));
      node.addEventListener('click', function () {
        if (lock || node.classList.contains('on') || node.classList.contains('gone')) return;
        node.classList.add('on');
        open.push({ c: c, node: node });
        if (open.length < 2) return;
        flips++; A.textContent = String(flips);
        var a = open[0], b2 = open[1];
        if (a.c.i === b2.c.i && a.c.side !== b2.c.side) {
          a.node.classList.add('gone'); b2.node.classList.add('gone');
          open = []; found++;
          C.textContent = String(found); B.textContent = String(pairs - found);
          if (found === pairs) {
            var r = keep('flips', flips, false);
            finish('다 맞히셨습니다 · ' + flips + '번 만에',
              r && r.was != null
                ? (r.better ? '지난 기록 ' + r.was + '번보다 빨랐습니다.'
                            : '가장 잘하셨을 때는 ' + r.was + '번이었습니다.')
                : (flips <= best ? '아주 잘하셨습니다.' : '한 번 더 하시면 더 줄어듭니다.'),
              [['뒤집은 횟수', flips], ['맞힌 짝', pairs], ['가장 잘한 것', (r && r.was != null ? Math.min(r.was, flips) : flips) + '번']]);
          }
        } else {
          lock = true;
          setTimeout(function () {
            a.node.classList.remove('on'); b2.node.classList.remove('on');
            open = []; lock = false;
          }, 700);
        }
      });
      board.appendChild(node);
    });
  }

  /* ── 1분 스피드 ────────────────────────────────────────────────── */
  function speed() {
    AL.textContent = '점수'; BL.textContent = '남은 시간'; CL.textContent = '연속';
    var score = 0, combo = 0, left = 60, at = 0, order = shuffle(EN.map(function (_, i) { return i; }));
    board.className = 'g-board g-speed';
    A.textContent = '0'; C.textContent = '0';

    var timer = setInterval(function () {
      left--; B.textContent = String(left);
      if (left <= 0) {
        clearInterval(timer);
        board.innerHTML = '';
        var r = keep('score', score, true);
        finish('1분 끝 · ' + score + '점',
          r && r.was != null
            ? (r.better ? '지난 기록 ' + r.was + '점을 넘었습니다.'
                        : '가장 잘하셨을 때는 ' + r.was + '점이었습니다.')
            : '한 번 더 하시면 더 오릅니다.',
          [['점수', score], ['푼 문제', at], ['가장 잘한 것', (r && r.was != null ? Math.max(r.was, score) : score) + '점']]);
      }
    }, 1000);
    B.textContent = String(left);

    function ask() {
      if (left <= 0) return;
      var me = order[at % order.length]; at++;
      var wrong = shuffle(KO.map(function (_, i) { return i; })
        .filter(function (i) { return i !== me; })).slice(0, 3);
      var opts = shuffle([me].concat(wrong));
      board.innerHTML = '';
      board.appendChild(el('div', 'sp-word', EN[me]));
      var box = el('div', 'sp-opts');
      opts.forEach(function (i) {
        var b3 = el('button', 'sp-opt', KO[i]);
        b3.type = 'button';
        b3.addEventListener('click', function () {
          if (left <= 0) return;
          if (i === me) {
            combo++;
            score += 10 * Math.min(5, combo);
            b3.classList.add('good');
          } else {
            combo = 0;
            b3.classList.add('bad');
          }
          A.textContent = String(score); C.textContent = String(combo);
          setTimeout(ask, 220);
        });
        box.appendChild(b3);
      });
      board.appendChild(box);
    }
    ask();
  }

  /* ── 철자 타자 ─────────────────────────────────────────────────── */
  function typing() {
    AL.textContent = '맞힌 개수'; BL.textContent = '걸린 시간'; CL.textContent = '남은 단어';
    var order = shuffle(EN.map(function (_, i) { return i; })).slice(0, Math.min(10, EN.length));
    var at = 0, hits = 0, t0 = Date.now(), timer;
    board.className = 'g-board g-type';
    A.textContent = '0'; C.textContent = String(order.length);

    timer = setInterval(function () {
      B.textContent = Math.round((Date.now() - t0) / 1000) + '초';
    }, 200);

    function ask() {
      if (at >= order.length) {
        clearInterval(timer);
        var secs = Math.round((Date.now() - t0) / 1000);
        board.innerHTML = '';
        var r = keep('secs', secs, false);
        finish('다 치셨습니다 · ' + secs + '초',
          r && r.was != null
            ? (r.better ? '지난 기록 ' + r.was + '초보다 빨랐습니다.'
                        : '가장 빨랐을 때는 ' + r.was + '초였습니다.')
            : (secs <= best ? '손이 빠르십니다.' : '한 번 더 하시면 줄어듭니다.'),
          [['걸린 시간', secs + '초'], ['맞힌 개수', hits], ['가장 빠른 것', (r && r.was != null ? Math.min(r.was, secs) : secs) + '초']]);
        return;
      }
      var me = order[at];
      C.textContent = String(order.length - at);
      board.innerHTML = '';
      board.appendChild(el('div', 'ty-ko', KO[me]));
      var hint = el('div', 'ty-hint');
      EN[me].split('').forEach(function (ch) { hint.appendChild(el('i', '', ch)); });
      board.appendChild(hint);
      var input = el('input', 'ty-in');
      input.type = 'text';
      input.autocapitalize = 'off';
      input.autocomplete = 'off';
      input.spellcheck = false;
      input.setAttribute('aria-label', '철자를 치세요');
      board.appendChild(input);
      input.focus();
      input.addEventListener('input', function () {
        var v = input.value;
        var want = EN[me];
        [].forEach.call(hint.children, function (n, i) {
          n.className = i < v.length ? (v[i] === want[i] ? 'ok' : 'no') : '';
        });
        if (v.toLowerCase() === want.toLowerCase()) {
          hits++; at++; A.textContent = String(hits);
          setTimeout(ask, 180);
        }
      });
    }
    ask();
  }

  var start = { match: match, speed: speed, type: typing }[kind] || match;
  function run() { done.hidden = true; start(); }
  document.getElementById('again').addEventListener('click', run);
  document.getElementById('retry').addEventListener('click', run);
  run();
})();
