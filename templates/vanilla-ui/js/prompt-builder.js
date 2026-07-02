(function () {
  var map = window.promptMap;
  if (!map) return;

  var taskEl = document.getElementById("prompt-task");
  var outputEl = document.getElementById("prompt-output");
  var skillsRoot = document.getElementById("prompt-skills");
  var rulesRoot = document.getElementById("prompt-rules-context");
  var rulesAlwaysRoot = document.getElementById("prompt-rules-always");
  var phrasesRoot = document.getElementById("prompt-phrases");
  var includeRulesEl = document.getElementById("prompt-include-rules");
  var copyBtn = document.getElementById("prompt-copy");
  var clearBtn = document.getElementById("prompt-clear");
  var copyStatus = document.getElementById("prompt-copy-status");

  var selectedSkillId = null;
  var selectedRules = new Set();

  function skillById(id) {
    return map.skills.find(function (s) {
      return s.id === id;
    });
  }

  function ruleById(id) {
    return map.rules.find(function (r) {
      return r.id === id;
    });
  }

  function renderAlwaysRules() {
    rulesAlwaysRoot.innerHTML = "";
    map.rules
      .filter(function (r) {
        return r.scope === "always";
      })
      .forEach(function (rule) {
        var badge = document.createElement("span");
        badge.className = "badge badge--primary";
        badge.textContent = rule.id;
        badge.title = rule.summary;
        rulesAlwaysRoot.appendChild(badge);
      });
  }

  function renderContextRules() {
    rulesRoot.innerHTML = "";
    map.rules
      .filter(function (r) {
        return r.scope !== "always";
      })
      .forEach(function (rule) {
        var label = document.createElement("label");
        label.className = "checkbox";

        var input = document.createElement("input");
        input.type = "checkbox";
        input.className = "checkbox__input";
        input.value = rule.id;
        input.checked = selectedRules.has(rule.id);
        input.addEventListener("change", function () {
          if (input.checked) selectedRules.add(rule.id);
          else selectedRules.delete(rule.id);
          saveState();
          updateOutput();
        });

        var text = document.createElement("span");
        text.textContent = rule.id + " — " + rule.summary;

        label.appendChild(input);
        label.appendChild(text);
        rulesRoot.appendChild(label);
      });
  }

  function renderSkills() {
    skillsRoot.innerHTML = "";
    var groups = ["active", "consumer", "planned"];

    groups.forEach(function (group) {
      var items = map.skills.filter(function (s) {
        return s.group === group;
      });
      if (!items.length) return;

      var groupEl = document.createElement("div");
      groupEl.className = "prompt-builder__skill-group";

      var title = document.createElement("h3");
      title.className = "prompt-builder__skill-group-title";
      title.textContent = map.groupLabels[group] || group;
      groupEl.appendChild(title);

      var list = document.createElement("div");
      list.className = "prompt-builder__skill-list";

      items.forEach(function (skill) {
        var label = document.createElement("label");
        label.className =
          "prompt-builder__skill" +
          (skill.group === "planned" ? " prompt-builder__skill--planned" : "");

        var input = document.createElement("input");
        input.type = "radio";
        input.name = "prompt-skill";
        input.className = "prompt-builder__skill-input";
        input.value = skill.id;
        input.checked = selectedSkillId === skill.id;
        input.addEventListener("change", function () {
          selectSkill(skill.id);
        });

        var body = document.createElement("div");
        body.className = "prompt-builder__skill-body";

        var nameRow = document.createElement("div");
        nameRow.className = "prompt-builder__skill-name";
        nameRow.innerHTML =
          "<code>" +
          skill.id +
          "</code>" +
          (skill.phase !== "—"
            ? '<span class="badge">' + skill.phase + "</span>"
            : "");

        var when = document.createElement("p");
        when.className = "prompt-builder__skill-when";
        when.textContent = skill.when;

        body.appendChild(nameRow);
        body.appendChild(when);
        label.appendChild(input);
        label.appendChild(body);
        list.appendChild(label);
      });

      groupEl.appendChild(list);
      skillsRoot.appendChild(groupEl);
    });
  }

  function renderPhrases() {
    phrasesRoot.innerHTML = "";
    map.phrases.forEach(function (phrase) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "badge prompt-builder__phrase";
      btn.textContent = phrase.text;
      btn.addEventListener("click", function () {
        taskEl.value = phrase.text;
        selectSkill(phrase.skill);
        taskEl.focus();
      });
      phrasesRoot.appendChild(btn);
    });
  }

  function applySkillRules(skill) {
    selectedRules.clear();
    if (!skill || !skill.rules) return;
    skill.rules.forEach(function (id) {
      selectedRules.add(id);
    });
    renderContextRules();
  }

  function selectSkill(id) {
    selectedSkillId = id;
    var skill = skillById(id);
    applySkillRules(skill);

    var radios = skillsRoot.querySelectorAll('input[name="prompt-skill"]');
    radios.forEach(function (radio) {
      radio.checked = radio.value === id;
    });

    saveState();
    updateOutput();
  }

  function buildPrompt() {
    var task = taskEl.value.trim();
    var lines = [];

    if (task) {
      lines.push(task);
      lines.push("");
    }

    if (selectedSkillId) {
      var skill = skillById(selectedSkillId);
      if (skill) {
        lines.push("Skill: `" + skill.id + "`");
        lines.push("Когда: " + skill.when);
        if (skill.path && skill.path !== "planned") {
          lines.push("Путь: `" + skill.path + "`");
        }
        lines.push("");
      }
    }

    if (includeRulesEl.checked) {
      var always = map.rules.filter(function (r) {
        return r.scope === "always";
      });
      if (always.length) {
        lines.push("Rules (always):");
        always.forEach(function (rule) {
          lines.push("- `" + rule.id + "` — " + rule.summary);
        });
        lines.push("");
      }

      var context = map.rules.filter(function (r) {
        return r.scope !== "always" && selectedRules.has(r.id);
      });
      if (context.length) {
        lines.push("Rules (контекст):");
        context.forEach(function (rule) {
          lines.push("- `" + rule.id + "` — " + rule.summary);
        });
        lines.push("");
      }
    } else if (selectedRules.size) {
      var ids = Array.from(selectedRules).sort();
      lines.push("Учитывай rules: " + ids.map(function (id) { return "`" + id + "`"; }).join(", "));
      lines.push("");
    }

    if (!task && !selectedSkillId) {
      return "Выбери skill и опиши задачу — или нажми быструю фразу выше.";
    }

    if (!task && selectedSkillId) {
      lines.push("_(добавь описание задачи в поле «Задача»)_");
    }

    return lines.join("\n").trim();
  }

  function updateOutput() {
    outputEl.value = buildPrompt();
  }

  function saveState() {
    try {
      localStorage.setItem(
        "prompt-builder",
        JSON.stringify({
          task: taskEl.value,
          skill: selectedSkillId,
          rules: Array.from(selectedRules),
          includeRules: includeRulesEl.checked,
        })
      );
    } catch (_e) {
      /* ignore */
    }
  }

  function loadState() {
    try {
      var storedJson = localStorage.getItem("prompt-builder");
      if (!storedJson) return;
      var state = JSON.parse(storedJson);
      if (state.task) taskEl.value = state.task;
      if (typeof state.includeRules === "boolean") {
        includeRulesEl.checked = state.includeRules;
      }
      if (Array.isArray(state.rules)) {
        selectedRules = new Set(state.rules);
      }
      if (state.skill && skillById(state.skill)) {
        selectedSkillId = state.skill;
      }
    } catch (_e) {
      /* ignore */
    }
  }

  taskEl.addEventListener("input", function () {
    saveState();
    updateOutput();
  });

  includeRulesEl.addEventListener("change", function () {
    saveState();
    updateOutput();
  });

  copyBtn.addEventListener("click", function () {
    var text = outputEl.value;
    if (!text || text.startsWith("Выбери skill")) {
      copyStatus.textContent = "Нечего копировать";
      return;
    }
    navigator.clipboard.writeText(text).then(
      function () {
        copyStatus.textContent = "Скопировано в буфер";
        setTimeout(function () {
          copyStatus.textContent = "";
        }, 2000);
      },
      function () {
        outputEl.select();
        copyStatus.textContent = "Выделено — Cmd/Ctrl+C";
      }
    );
  });

  clearBtn.addEventListener("click", function () {
    taskEl.value = "";
    selectedSkillId = null;
    selectedRules.clear();
    var radios = skillsRoot.querySelectorAll('input[name="prompt-skill"]');
    radios.forEach(function (radio) {
      radio.checked = false;
    });
    renderContextRules();
    saveState();
    updateOutput();
    copyStatus.textContent = "";
  });

  loadState();
  renderAlwaysRules();
  renderContextRules();
  renderSkills();
  renderPhrases();
  updateOutput();
})();
