/* 학습 결과 카드.
   다 푼 자리에서 그림 한 장을 만들어 드립니다. 저장하거나 그대로 공유하실 수
   있습니다. 이름도 성적도 서버로 안 보냅니다 — 이 브라우저 안에서 그려서
   이 브라우저 안에 저장할 뿐이라 개인정보가 생기지 않습니다. */
window.OrticaCard = (function () {
  var W = 1080, H = 1600, MIN_H = 1080;
  var BRAND = '#146b4a', DARK = '#0e4d35', SOFT = '#e8f2ec', INK = '#1a1d21';
  var MUTED = '#6b7280', LINE = '#dfe6e2';

  function font(weight, size) {
    return weight + ' ' + size + 'px "NanumSquareRound", system-ui, sans-serif';
  }
  function round(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  /* 한글은 어절 중간에서 자르면 읽기 나쁩니다. 띄어쓰기에서만 접습니다. */
  function wrap(ctx, text, max) {
    var words = String(text || '').split(' '), lines = [], line = '';
    words.forEach(function (w) {
      var t = line ? line + ' ' + w : w;
      if (ctx.measureText(t).width > max && line) { lines.push(line); line = w; }
      else line = t;
    });
    if (line) lines.push(line);
    return lines;
  }
  function today() {
    var d = new Date();
    return d.getFullYear() + '. ' + (d.getMonth() + 1) + '. ' + d.getDate() + '.';
  }

  /* 내용을 한 번 재 보고, 그 높이에 맞춰 다시 그립니다. 잔 숫자가 없거나
     제목이 짧으면 카드 아래가 휑하게 비는 것을 막으려는 것입니다. */
  function draw(canvas, d) {
    var probe = document.createElement('canvas');
    probe.width = W; probe.height = H;
    var need = body(probe.getContext('2d'), d, false);
    canvas.width = W;
    canvas.height = Math.max(MIN_H, Math.min(H, Math.round(need + 150)));
    body(canvas.getContext('2d'), d, true);
    return canvas;
  }

  function body(ctx, d, paint) {
    var H2 = ctx.canvas.height;
    if (paint) {
      ctx.fillStyle = '#fbfdfc'; ctx.fillRect(0, 0, W, H2);
      ctx.fillStyle = BRAND; ctx.fillRect(0, 0, W, 14);
    }
    var pad = 88, y = 150;

    // 브랜드
    ctx.font = font(900, 40);
    if (paint) { ctx.fillStyle = BRAND; ctx.fillText(d.brand || '오르티카잉', pad, y); }
    y += 78;

    // 무엇을 했는지 — 알약
    if (d.kind) {
      ctx.font = font(800, 30);
      var kw = ctx.measureText(d.kind).width;
      if (paint) {
        ctx.fillStyle = SOFT; round(ctx, pad, y - 34, kw + 44, 54, 27); ctx.fill();
        ctx.fillStyle = DARK; ctx.fillText(d.kind, pad + 22, y + 2);
      }
      y += 88;
    }

    // 제목
    ctx.fillStyle = INK; ctx.font = font(900, 58);
    wrap(ctx, d.title, W - pad * 2).slice(0, 2).forEach(function (line) {
      if (paint) ctx.fillText(line, pad, y);
      y += 74;
    });
    if (d.scope) {
      ctx.fillStyle = MUTED; ctx.font = font(500, 32);
      if (paint) ctx.fillText(String(d.scope).slice(0, 40), pad, y + 6);
      y += 50;
    }

    // 큰 숫자
    y += 60;
    ctx.textAlign = 'center';
    ctx.fillStyle = BRAND; ctx.font = font(900, 168);
    if (paint) ctx.fillText(d.big, W / 2, y + 120);
    y += 190;
    if (d.say) {
      ctx.fillStyle = INK; ctx.font = font(700, 38);
      wrap(ctx, d.say, W - pad * 2).slice(0, 2).forEach(function (line) {
        if (paint) ctx.fillText(line, W / 2, y + 30);
        y += 52;
      });
      y += 20;
    }
    ctx.textAlign = 'left';

    // 잔 숫자들
    var stats = (d.stats || []).slice(0, 3);
    if (stats.length) {
      y += 40;
      var boxW = (W - pad * 2 - 24 * (stats.length - 1)) / stats.length;
      stats.forEach(function (s, i) {
        var x = pad + i * (boxW + 24);
        if (!paint) return;
        ctx.fillStyle = '#fff'; round(ctx, x, y, boxW, 150, 22); ctx.fill();
        ctx.strokeStyle = LINE; ctx.lineWidth = 2; ctx.stroke();
        ctx.textAlign = 'center';
        ctx.fillStyle = INK; ctx.font = font(900, 54);
        ctx.fillText(String(s[1]), x + boxW / 2, y + 82);
        ctx.fillStyle = MUTED; ctx.font = font(600, 26);
        ctx.fillText(String(s[0]), x + boxW / 2, y + 122);
        ctx.textAlign = 'left';
      });
      y += 190;
    }

    if (d.streak) {
      ctx.font = font(800, 32);
      var sw = ctx.measureText(d.streak).width;
      if (paint) {
        ctx.fillStyle = '#fff5e8'; round(ctx, pad, y - 34, sw + 44, 56, 28); ctx.fill();
        ctx.fillStyle = '#9a5b12'; ctx.fillText(d.streak, pad + 22, y + 4);
      }
      y += 40;
    }

    if (!paint) return y;                 // 재는 것으로 끝

    // 발밑
    ctx.fillStyle = MUTED; ctx.font = font(500, 28);
    ctx.fillText(today(), pad, H2 - 66);
    if (d.site) {
      ctx.textAlign = 'right';
      ctx.fillStyle = BRAND; ctx.font = font(800, 28);
      ctx.fillText(d.site, W - pad, H2 - 66);
      ctx.textAlign = 'left';
    }
    return y;
  }

  function filename(d) {
    var name = (d.title || '학습결과').replace(/[\\/:*?"<>|]/g, '').slice(0, 40);
    return name + ' 결과.png';
  }

  /* 카드 한 장과 단추 둘을 그 자리에 붙입니다. */
  function attach(box, d) {
    if (!box || box.dataset.made) return;
    box.dataset.made = '1';
    box.innerHTML =
      '<h3 class="rc-head">오늘 한 것, 카드로 남기기</h3>' +
      '<p class="rc-say muted">그림 한 장으로 저장됩니다. 이름도 성적도 아무 데도 안 보냅니다.</p>' +
      '<canvas class="rc-canvas" aria-label="학습 결과 카드"></canvas>' +
      '<div class="rc-acts">' +
      '  <button type="button" class="btn btn-primary rc-save">이미지로 저장</button>' +
      '  <button type="button" class="btn btn-ghost rc-share" hidden>공유하기</button>' +
      '</div>';
    var canvas = box.querySelector('.rc-canvas');
    var go = function () { draw(canvas, d); };
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(go);
    else go();
    go();

    box.querySelector('.rc-save').addEventListener('click', function () {
      canvas.toBlob(function (blob) {
        if (!blob) return;
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url; a.download = filename(d);
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
      }, 'image/png');
    });

    /* 폰에서는 저장보다 바로 보내는 쪽이 훨씬 편합니다. */
    var share = box.querySelector('.rc-share');
    if (navigator.canShare && navigator.share) {
      try {
        var probe = new File([new Blob()], 'x.png', { type: 'image/png' });
        if (navigator.canShare({ files: [probe] })) share.hidden = false;
      } catch (e) { /* 못 보내면 저장 단추만 둡니다 */ }
    }
    share.addEventListener('click', function () {
      canvas.toBlob(function (blob) {
        if (!blob) return;
        var file = new File([blob], filename(d), { type: 'image/png' });
        navigator.share({ files: [file], title: d.title || '학습 결과' })
          .catch(function () { /* 취소하신 것입니다 */ });
      }, 'image/png');
    });
    return canvas;
  }

  return { draw: draw, attach: attach };
})();
