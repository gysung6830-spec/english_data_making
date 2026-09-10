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

  /* ── 단어 비 ───────────────────────────────────────────────────
     단어가 위에서 떨어집니다. 아래 뜻에 맞는 것을 눌러 터뜨리세요.
     카드 위치를 외우는 게임이 아니라 단어를 알아야 하는 게임입니다. */
  function rain() {
    AL.textContent = '점수'; BL.textContent = '목숨'; CL.textContent = '연속';
    board.className = 'g-board g-rain';
    board.innerHTML = '<div class="rn-sky" id="rnSky"></div>' +
                      '<div class="rn-ask">이 뜻을 찾으세요' +
                      '<b id="rnWant">…</b></div>';
    var sky = document.getElementById('rnSky');
    var want = document.getElementById('rnWant');

    var score = 0, combo = 0, lives = 3, cleared = 0;
    var drops = [], target = null, alive = true, last = 0, spawnAt = 0;
    var order = shuffle(EN.map(function (_, i) { return i; }));
    var at = 0;
    A.textContent = '0'; B.textContent = '❤❤❤'; C.textContent = '0';

    function speed() { return 0.020 + Math.min(0.045, cleared * 0.0016); }
    function gap() { return Math.max(700, 1600 - cleared * 45); }

    /* 아무 데나 떨어뜨리면 글자끼리 겹쳐 못 읽습니다. 자리를 넷으로 나누고,
       그 가운데 가장 비어 있는 자리에 내려 줍니다. */
    var LANES = [4, 28, 52, 74];

    function freeLane() {
      var best = 0, room = -1;
      LANES.forEach(function (x, i) {
        var mine = drops.filter(function (d) { return d.lane === i; });
        var top = mine.length ? Math.min.apply(null, mine.map(function (d) { return d.y; })) : 999;
        if (top > room) { room = top; best = i; }
      });
      return best;
    }

    function spawn(startY) {
      if (drops.length >= 6) return;
      var me = order[at % order.length]; at++;
      var lane = freeLane();
      var node = el('button', 'rn-drop', EN[me]);
      node.type = 'button';
      node.style.left = LANES[lane] + '%';
      node.addEventListener('click', function () { hit(one); });
      var one = { i: me, y: (startY == null ? -10 : startY), lane: lane, node: node };
      node.style.top = one.y + '%';
      sky.appendChild(node);
      drops.push(one);
      if (!target) aim();
    }

    function aim() {
      // 어느 것이 답인지 표시하지 않습니다. 표시하면 단어를 몰라도 이겨서,
      // 카드 뒤집기 게임을 뺀 것과 같은 일이 됩니다.
      target = drops.length ? drops[Math.floor(Math.random() * drops.length)] : null;
      want.textContent = target ? KO[target.i] : '…';
    }

    function drop(one, why) {
      one.node.classList.add(why);
      var node = one.node;
      setTimeout(function () { if (node.parentNode) node.parentNode.removeChild(node); }, 260);
      drops = drops.filter(function (d) { return d !== one; });
      // 다 터뜨려 빈 하늘이 되면 곧바로 하나 내려 줍니다. 안 그러면 다음
      // 것이 나올 때까지 '…' 만 뜬 채로 몇 초를 기다리게 됩니다.
      if (!drops.length && alive) { spawn(); spawnAt = performance.now() + gap(); }
      if (one === target) { target = null; aim(); }
    }

    function hit(one) {
      if (!alive) return;
      if (one !== target) {
        combo = 0; C.textContent = '0';
        one.node.classList.add('miss');
        setTimeout(function () { one.node.classList.remove('miss'); }, 300);
        return;
      }
      combo++; cleared++;
      score += 10 * Math.min(5, combo);
      A.textContent = String(score); C.textContent = String(combo);
      drop(one, 'pop');
    }

    function lose(one) {
      lives--; combo = 0;
      B.textContent = '❤'.repeat(Math.max(0, lives)) || '—';
      C.textContent = '0';
      drop(one, 'fell');
      if (lives <= 0) over();
    }

    function over() {
      alive = false;
      drops.forEach(function (d) { if (d.node.parentNode) d.node.parentNode.removeChild(d.node); });
      drops = [];
      var r = keep('score', score, true);
      finish('끝 · ' + score + '점',
        r && r.was != null
          ? (r.better ? '지난 기록 ' + r.was + '점을 넘었습니다.'
                      : '가장 잘하셨을 때는 ' + r.was + '점이었습니다.')
          : '한 번 더 하시면 더 오릅니다.',
        [['점수', score], ['터뜨린 단어', cleared],
         ['가장 잘한 것', (r && r.was != null ? Math.max(r.was, score) : score) + '점']]);
    }

    function tick(now) {
      if (!alive) return;
      if (!last) last = now;
      var dt = Math.min(60, now - last);
      last = now;
      if (now > spawnAt) { spawn(); spawnAt = now + gap(); }
      var step = speed() * dt;
      drops.slice().forEach(function (one) {
        one.y += step;
        one.node.style.top = one.y + '%';
        if (one.y >= 88) lose(one);
      });
      requestAnimationFrame(tick);
    }
    // 처음부터 여럿 떠 있어야 고르는 맛이 납니다. 하나뿐이면 그냥 누르면 됩니다.
    // 높이를 엇갈리게 두어 한 줄로 나란히 서지 않게 합니다.
    [10, -12, -34, -56].forEach(function (y) { spawn(y); });
    requestAnimationFrame(tick);

    /* 시험에서 눌러 볼 수 있게 지금 상태를 내어 줍니다 */
    board.pick = function (right) {
      var one = right ? target : drops.filter(function (d) { return d !== target; })[0];
      if (!one) return false;
      one.node.click();
      return true;
    };
    board.sink = function () {
      if (!drops.length || !alive) return false;
      lose(drops[0]);
      return true;
    };
    board.state = function () {
      return { drops: drops.length, lives: lives, combo: combo, score: score,
               alive: alive, want: target ? KO[target.i] : '' };
    };
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

  var start = { rain: rain, speed: speed, type: typing }[kind] || rain;
  function run() { done.hidden = true; start(); }
  document.getElementById('again').addEventListener('click', run);
  document.getElementById('retry').addEventListener('click', run);
  run();
})();
