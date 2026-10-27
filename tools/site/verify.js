// verify.js: the site's "check a proof line" page.
//
// The same grammar, answers and words as `playnice verify`
// (tools/playnice/playnice.py: parse_verify_line and cmd_verify);
// tests/test_site.py runs both on the same lines and compares them.
// Data comes from verify.json, built from the floor. The receipt word is
// compared by its SHA-256 only, so the page never holds the word itself.
"use strict";

(function (root) {
  var WORD = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  var VERSION_SHAPE = /^\d+\.\d+(?:\.\d+)?$/;

  function splitLine(line) {
    return line.replace(/\s+[-|]\s+/g, " · ").split("·")
      .map(function (s) { return s.trim(); })
      .filter(function (s) { return s !== ""; });
  }

  function versionTuple(v) {
    var parts = v.split(".").map(Number);
    while (parts.length < 3) parts.push(0);
    return parts;
  }

  function compare(a, b) {
    for (var i = 0; i < 3; i++) {
      if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
    }
    return 0;
  }

  function canonicalId(id, data) {
    var ids = data.contract_ids;
    var mapped = ids.indexOf(id) >= 0 ? id : (data.aliases[id] || id);
    return ids.indexOf(mapped) >= 0 ? mapped : null;
  }

  function parse(line, data) {
    var segs = splitLine(line);
    if (!segs.length) return { problem: "the line is empty" };
    var m = /^Play-Nice floor (\S+)$/.exec(segs[0]);
    if (!m) return { problem: "the line must start with 'Play-Nice floor <version>', got '" + segs[0] + "'" };
    var version = m[1];
    if (!VERSION_SHAPE.test(version)) return { problem: "floor version must look like 1.0.0, got '" + version + "'" };
    if (segs.length < 2) return { problem: "no 'receipt <word>' part after the version" };
    m = /^receipt (\S+)$/.exec(segs[1]);
    if (!m) return { problem: "expected 'receipt <word>', got '" + segs[1] + "'" };
    var receipt = m[1];
    if (!WORD.test(receipt)) return { problem: "receipt word must be lowercase words joined with '-', got '" + receipt + "'" };
    var read = [];
    if (segs.length > 2) {
      if (segs.length > 3) return { problem: "too many parts; the line ends with the optional 'read <id>, <id>'" };
      m = /^read ([\s\S]*)$/.exec(segs[2]);
      if (!m) return { problem: "expected 'read <id>, <id>', got '" + segs[2] + "'" };
      read = m[1].split(",").map(function (p) { return p.trim(); }).filter(function (p) { return p; });
      if (!read.length) return { problem: "'read' has no contract ids after it" };
      var bad = read.filter(function (id) { return !WORD.test(id); });
      if (bad.length) return { problem: "read ids must be lowercase ids like 'web-ui': " + bad.join(", ") };
      var unknown = read.filter(function (id) { return canonicalId(id, data) === null; });
      if (unknown.length) {
        return { problem: "unknown read ids (not library contracts, not aliases): " + unknown.join(", ") };
      }
    }
    return { parsed: { version: version, receipt: receipt, read: read } };
  }

  // sha256hex(text) returns a Promise of the lowercase hex digest.
  function verify(line, data, sha256hex) {
    line = (line || "").trim();
    var floor = data.floor_version;
    var r = parse(line, data);
    if (r.problem) {
      return Promise.resolve({
        state: "INVALID", message: r.problem,
        next: "copy the version, the receipt word and the ids from the pages you actually read"
      });
    }
    var given = r.parsed;
    var order = compare(versionTuple(given.version), versionTuple(floor));
    return sha256hex(given.receipt).then(function (digest) {
      if (order === 0 && digest === data.receipt_sha256) {
        return { state: "CURRENT", message: "floor " + floor + " and the receipt word match this library", next: "keep working" };
      }
      if (order === 0) {
        return { state: "INVALID", message: "that receipt word is not on floor " + floor,
          next: "read " + data.floor_path + " and copy the receipt word from it" };
      }
      if (order > 0) {
        return { state: "INVALID",
          message: "floor " + given.version + " is newer than this library's floor " + floor + ", so it cannot be checked here",
          next: "if you read a newer floor, update this library (git pull); otherwise copy the version and receipt word from " + data.floor_path };
      }
      return { state: "OUT_OF_DATE", message: "floor is now " + floor + ", read " + data.floor_path,
        next: "re-read that page and write a fresh line from it" };
    });
  }

  var api = { parse: parse, verify: verify, splitLine: splitLine };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
    return;
  }

  // ---- the page

  var HEADS = { CURRENT: "CURRENT", OUT_OF_DATE: "OUT OF DATE", INVALID: "INVALID" };

  function browserSha256(text) {
    var bytes = new TextEncoder().encode(text);
    return root.crypto.subtle.digest("SHA-256", bytes).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return ("0" + b.toString(16)).slice(-2);
      }).join("");
    });
  }

  function show(box, state, message, next) {
    box.hidden = false;
    box.className = "result " + state.toLowerCase().replace(/_/g, "-");
    box.textContent = "";
    var head = document.createElement("p");
    var strong = document.createElement("strong");
    strong.textContent = HEADS[state] || state;
    head.appendChild(strong);
    head.appendChild(document.createTextNode(": " + message));
    box.appendChild(head);
    if (next) {
      var p = document.createElement("p");
      p.textContent = "Next: " + next;
      box.appendChild(p);
    }
  }

  function start() {
    var form = document.getElementById("verify-form");
    var input = document.getElementById("line");
    var box = document.getElementById("result");
    if (!form || !input || !box) return;
    var dataPromise = null;
    function data() {
      if (!dataPromise) {
        dataPromise = fetch("verify.json").then(function (r) {
          if (!r.ok) throw new Error("verify.json answered HTTP " + r.status);
          return r.json();
        });
      }
      return dataPromise;
    }
    function check() {
      if (!(root.crypto && root.crypto.subtle)) {
        show(box, "INVALID", "this browser cannot compute SHA-256 on this page",
          "run playnice verify \"<the line>\" instead");
        return;
      }
      data().then(function (d) {
        return verify(input.value, d, browserSha256);
      }).then(function (out) {
        show(box, out.state, out.message, out.next);
      }).catch(function (err) {
        show(box, "INVALID", "could not load the floor data (" + err.message + ")",
          "reload the page, or run playnice verify \"<the line>\"");
      });
    }
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      check();
    });
    var given = new URLSearchParams(root.location.search).get("line");
    if (given) {
      input.value = given;
      check();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})(typeof window !== "undefined" ? window : globalThis);
