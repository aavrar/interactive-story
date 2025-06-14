// App.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

// --- Tutorial Component ---
const CLASSES = [
  { name: "Wanderer", desc: "Balanced stats, good at exploring." },
  { name: "Mystic", desc: "High magic, low strength." },
  { name: "Warrior", desc: "High strength, low magic." },
  { name: "Rogue", desc: "Stealthy and quick." }
];

function Tutorial({ onComplete, worldGenProgress, worldGenDone }) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [chosenClass, setChosenClass] = useState(CLASSES[0].name);
  const [showClassDesc, setShowClassDesc] = useState(false);

  const next = () => setStep(s => s + 1);

  return (
    <div className="tutorial-screen">
      <div className="scene scene-fade in">
        <div className="description">
          {step === 0 && (
            <>
              <h2>Forest Clearing</h2>
              <p>
                You awaken in a misty forest clearing. A gentle light filters through the trees.
                A mysterious figure in a glowing cloak stands before you.
              </p>
              <p>
                <span className="clickable-text npc" onClick={next}>Approach the guide</span>
              </p>
            </>
          )}
          {step === 1 && (
            <>
              <h2>The Guide</h2>
              <p>
                <b>Guide:</b> "Welcome, traveler. Before you begin your journey, tell me your <b>name</b>."
              </p>
              <form onSubmit={e => { e.preventDefault(); if (name) next(); }}>
                <input
                  className="tutorial-input"
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Enter your name..."
                  autoFocus
                />
                <button className="start-button" type="submit" disabled={!name}>Continue</button>
              </form>
            </>
          )}
          {step === 2 && (
            <>
              <h2>Choose Your Class</h2>
              <p>
                <b>Guide:</b> "Every adventurer has a calling. What <b>class</b> do you feel drawn to?"
              </p>
              <div className="class-choices">
                {CLASSES.map(cls => (
                  <div
                    key={cls.name}
                    className={`class-choice${chosenClass === cls.name ? ' selected' : ''}`}
                    onClick={() => { setChosenClass(cls.name); setShowClassDesc(true); }}
                    tabIndex={0}
                    role="button"
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { setChosenClass(cls.name); setShowClassDesc(true); } }}
                  >
                    {cls.name}
                  </div>
                ))}
              </div>
              {showClassDesc && (
                <div className="class-desc">
                  {CLASSES.find(c => c.name === chosenClass).desc}
                </div>
              )}
              <button className="start-button" style={{ marginTop: 16 }} onClick={next}>Confirm</button>
            </>
          )}
          {step === 3 && (
            <>
              <h2>How to Play</h2>
              <p>
                <b>Guide:</b> "This world responds to your <b>commands</b>. Try moving by typing <span className="clickable-text choice">go north</span> or by <span className="clickable-text choice">clicking on actions</span>."
              </p>
              <p>
                "To pick up items, type <span className="clickable-text item">take torch</span> or click on the item name."
              </p>
              <p>
                "To talk to people, type <span className="clickable-text npc">talk to guide</span> or click on their name."
              </p>
              <button className="start-button" onClick={next}>Continue</button>
            </>
          )}
          {step === 4 && (
            <>
              <h2>Ready?</h2>
              <p>
                <b>Guide:</b> "Are you ready to begin your adventure, <b>{name}</b> the <b>{chosenClass}</b>?"
              </p>
              <button
                className="start-button"
                onClick={() => onComplete({ name, chosenClass })}
                disabled={!worldGenDone}
                style={worldGenDone ? {} : { opacity: 0.6, cursor: 'not-allowed' }}
              >
                {worldGenDone ? "Enter the World" : `Preparing the world... (${worldGenProgress}%)`}
              </button>
              {!worldGenDone && (
                <div className="tutorial-progress-bar-outer">
                  <div className="tutorial-progress-bar" style={{ width: `${worldGenProgress}%` }} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// --- TypewriterText Component with Sound ---
function TypewriterText({ text, speed = 20, onDone }) {
  const [displayed, setDisplayed] = useState('');
  const indexRef = useRef(0);
  const typeSound = useRef(null);

  useEffect(() => {
    setDisplayed('');
    indexRef.current = 0;
    if (!text) return;

    if (!typeSound.current) {
      typeSound.current = new window.Audio('/sounds/type.wav');
      typeSound.current.volume = 0.08;
    }

    const interval = setInterval(() => {
      setDisplayed((prev) => {
        const next = text.slice(0, indexRef.current + 1);
        indexRef.current += 1;
        if (next.length <= text.length && typeSound.current) {
          typeSound.current.currentTime = 0;
          typeSound.current.play();
        }
        if (next.length >= text.length) {
          clearInterval(interval);
          if (onDone) onDone();
        }
        return next;
      });
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, onDone]);

  return <span>{displayed}</span>;
}

function ProgressBar({ loading, progress }) {
  if (!loading && progress === 0) return null;
  return (
    <div className="progress-bar-outer">
      <div className="progress-bar-container">
        <div
          className="progress-bar"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="progress-bar-label">{Math.round(progress)}%</div>
    </div>
  );
}

function LoadingScreen({ progress, loading, onStart }) {
  return (
    <div className={`loading-screen${loading ? ' loading-intense' : ''}`}>
      <div className="crt-overlay"></div>
      <div className="loading-content">
        <h1 className="loading-title">Plot Generator</h1>
        <div className="loading-backstory">
          <p>
            You wake in a clearing surrounded by a forest, but don't remember how you got here. You don't remember
            how you got here, in fact you don't remember anything. Who are you? How did you get here? 
            All will come to those who wait. For now, you are a lone wanderer.
            Every step forward is a step deeper into the unknown. 
            Will you survive the darkness, or become just another legend whispered among the trees?
          </p>
        </div>
        <ProgressBar loading={loading} progress={progress} />
        {progress >= 100 && !loading && (
          <button className="start-button" onClick={onStart}>
            Start Adventure
          </button>
        )}
      </div>
    </div>
  );
}

function BootScreen({ messages, step }) {
  return (
    <div className="loading-screen loading-intense">
      <div className="crt-overlay"></div>
      <div className="loading-content boot-sequence">
        <pre className="boot-messages">
          {messages.slice(0, step).map((msg, i) => (
            <div key={i} className="boot-line">{msg}</div>
          ))}
          {step < messages.length && <span className="boot-cursor">█</span>}
        </pre>
      </div>
    </div>
  );
}

function getSceneBgClass(scene) {
  if (!scene || !scene.scene_id) return '';
  if (scene.scene_id.includes('forest')) return 'bg-forest';
  if (scene.scene_id.includes('cave')) return 'bg-cave';
  if (scene.scene_id.includes('village')) return 'bg-village';
  if (scene.scene_id.includes('mountain')) return 'bg-mountain';
  if (scene.scene_id.includes('ruin')) return 'bg-ruins';
  if (scene.scene_id.includes('castle')) return 'bg-castle';
  return '';
}

async function getIntent(command, backendURL) {
  const response = await fetch(`${backendURL}/intent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: command })
  });
  const data = await response.json();
  return data.intent;
}

function App() {
  const [scene, setScene] = useState(null);
  const [command, setCommand] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(true);
  const [conversationText, setConversationText] = useState('');
  const [progress, setProgress] = useState(0);
  const [showLoadingScreen, setShowLoadingScreen] = useState(true);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [savesList, setSavesList] = useState([]);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [showTutorial, setShowTutorial] = useState(true);
  const [playerInfo, setPlayerInfo] = useState({ name: '', chosenClass: '' });

  // World generation progress state
  const [worldGenProgress, setWorldGenProgress] = useState(0);
  const [worldGenDone, setWorldGenDone] = useState(false);

  const bootMessages = [
    "Booting up Dark Forest Adventure OS v0.1.2...",
    "Initializing memory banks...",
    "Loading procedural templates...",
    "Establishing connection to story engine...",
    "Generating world seed...",
    "Loading locations, items, and NPCs...",
    "Applying CRT filters...",
    "Starting World Generation."
  ];
  const [bootStep, setBootStep] = useState(0);
  const [showBoot, setShowBoot] = useState(true);
  const [showHelp, setShowHelp] = useState(false);

  const [sceneKey, setSceneKey] = useState(0);
  const [sceneVisible, setSceneVisible] = useState(true);

  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [autocompleteOptions, setAutocompleteOptions] = useState([]);
  const [autocompleteIndex, setAutocompleteIndex] = useState(-1);

  const [newlyAddedItem, setNewlyAddedItem] = useState(null);

  const backendURL = process.env.REACT_APP_BACKEND_URL || 'https://interactive-story-o8z0.onrender.com';

  // --- World Generation in Background ---
  useEffect(() => {
    if (showTutorial) {
      // Start world generation as soon as tutorial starts
      let cancelled = false;
      setWorldGenProgress(0);
      setWorldGenDone(false);

      // Start the world generation process
      axios.post(`${backendURL}/start_new_run`, { name: "", chosenClass: "" })
        .then(() => {
          // Poll for progress
          const poll = () => {
            axios.get(`${backendURL}/status`)
              .then(res => {
                if (cancelled) return;
                // Simulate progress: if status is active, set to 100%
                if (res.data.status === "active") {
                  setWorldGenProgress(100);
                  setWorldGenDone(true);
                } else {
                  // Simulate progress bar (for demo, increment by 10% every 0.5s)
                  setWorldGenProgress(prev => {
                    if (prev < 90) return prev + 10;
                    return prev;
                  });
                  setTimeout(poll, 500);
                }
              })
              .catch(() => {
                if (!cancelled) setTimeout(poll, 700);
              });
          };
          poll();
        })
        .catch(() => {
          setWorldGenProgress(100);
          setWorldGenDone(true);
        });

      return () => { cancelled = true; };
    }
  }, [showTutorial, backendURL]);

  // --- After tutorial, set player info and fetch scene ---
  useEffect(() => {
    if (!showTutorial && playerInfo.name && playerInfo.chosenClass) {
      // Set player info and restart run with correct info
      axios.post(`${backendURL}/start_new_run`, {
        name: playerInfo.name,
        chosenClass: playerInfo.chosenClass
      }).then(() => {
        fetchScene();
      });
    }
    // eslint-disable-next-line
  }, [showTutorial, playerInfo]);

  const fetchScene = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${backendURL}/scene`);
      setSceneVisible(false);
      setTimeout(() => {
        if (scene && response.data && response.data.inventory) {
          const prevInv = scene.inventory || [];
          const newInv = response.data.inventory;
          const added = newInv.find(item => !prevInv.includes(item));
          setNewlyAddedItem(added || null);
          if (added) setTimeout(() => setNewlyAddedItem(null), 1200);
        }
        setScene(response.data);
        setSceneKey((k) => k + 1);
        setSceneVisible(true);
      }, 300);
      setError(null);
      setProgress(100);
      setLoading(false);
    } catch (error) {
      setError(error.response?.data?.detail || error.message);
      setScene(null);
      setProgress(0);
      setLoading(false);
    }
  };

  const handleCommandSubmit = async (event) => {
    event.preventDefault();
    let commandToSend = '';
    let isConversation = false;

    if (scene && scene.current_conversation) {
      commandToSend = conversationText.trim();
      isConversation = true;
    } else {
      commandToSend = command.trim();
    }

    if (!commandToSend) return;

    setCommandHistory((prev) => [...prev, commandToSend]);
    setHistoryIndex(-1);

    const intent = await getIntent(commandToSend, backendURL);
    console.log("Predicted intent:", intent);

    try {
      const response = await axios.post(`${backendURL}/command`, { command: commandToSend });

      if (isConversation) {
        setResult(response.data.result || 'Response processed');
        setConversationText('');
      } else {
        setResult(response.data.result || 'Command processed');
        setCommand('');
      }

      setError(null);

      setTimeout(() => {
        fetchScene();
      }, 500);

    } catch (error) {
      setError(error.response?.data?.detail || error.message);
      setResult('');
    }
  };

  // --- Clickable text handlers ---
  const handleChoiceClick = async (choice) => {
    setCommandHistory((prev) => [...prev, choice]);
    setHistoryIndex(-1);
    try {
      const response = await axios.post(`${backendURL}/command`, { command: choice });
      setResult(response.data.result || 'Command processed');
      setCommand('');
      setError(null);
      setTimeout(() => {
        fetchScene();
      }, 500);
    } catch (error) {
      setError(error.response?.data?.detail || error.message);
      setResult('');
    }
  };

  const handleItemClick = async (item) => {
    const takeCommand = `take ${item}`;
    setCommandHistory((prev) => [...prev, takeCommand]);
    setHistoryIndex(-1);
    try {
      const response = await axios.post(`${backendURL}/command`, { command: takeCommand });
      setResult(response.data.result || 'Item taken');
      setCommand('');
      setError(null);
      setTimeout(() => {
        fetchScene();
      }, 500);
    } catch (error) {
      setError(error.response?.data?.detail || error.message);
      setResult('');
    }
  };

  // --- Command Input Handlers ---
  const handleCommandChange = (event) => {
    setCommand(event.target.value);
  };

  const handleCommandKeyDown = (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex < 0 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setCommand(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex >= 0) {
        const newIndex = historyIndex + 1;
        if (newIndex < commandHistory.length) {
          setHistoryIndex(newIndex);
          setCommand(commandHistory[newIndex]);
        } else {
          setHistoryIndex(-1);
          setCommand('');
        }
      }
    }
    else if (e.key === 'Tab' && autocompleteOptions.length > 0) {
      e.preventDefault();
      setCommand(autocompleteOptions[autocompleteIndex >= 0 ? autocompleteIndex : 0]);
      setAutocompleteOptions([]);
      setAutocompleteIndex(-1);
    } else if (e.key === 'ArrowDown' && autocompleteOptions.length > 0) {
      e.preventDefault();
      setAutocompleteIndex((prev) => (prev + 1) % autocompleteOptions.length);
    } else if (e.key === 'ArrowUp' && autocompleteOptions.length > 0) {
      e.preventDefault();
      setAutocompleteIndex((prev) => (prev - 1 + autocompleteOptions.length) % autocompleteOptions.length);
    }
  };

  const handleConversationChange = (event) => {
    setConversationText(event.target.value);
  };

  useEffect(() => {
    if (showBoot && bootStep < bootMessages.length) {
      const timeout = setTimeout(() => {
        setBootStep(bootStep + 1);
      }, 700);
      return () => clearTimeout(timeout);
    } else if (showBoot && bootStep === bootMessages.length) {
      setTimeout(() => setShowBoot(false), 700);
    }
  }, [bootStep, showBoot]);

  useEffect(() => {
    if (!command) {
      setAutocompleteOptions([]);
      setAutocompleteIndex(-1);
      return;
    }
    if (scene && scene.choices) {
      const filtered = scene.choices.filter(choice =>
        choice.toLowerCase().startsWith(command.toLowerCase())
      );
      setAutocompleteOptions(filtered);
      setAutocompleteIndex(-1);
    }
  }, [command, scene]);

  if (showBoot) {
    return <BootScreen messages={bootMessages} step={bootStep} />;
  }

  if (showTutorial) {
    return (
      <Tutorial
        onComplete={({ name, chosenClass }) => {
          setPlayerInfo({ name, chosenClass });
          setShowTutorial(false);
        }}
        worldGenProgress={worldGenProgress}
        worldGenDone={worldGenDone}
      />
    );
  }

  if (showLoadingScreen) {
    return (
      <LoadingScreen
        progress={progress}
        loading={loading}
        onStart={() => {
          setShowLoadingScreen(false);
          setProgress(0);
          setLoading(false);
        }}
      />
    );
  }

  if (error) {
    return (
      <div className="App">
        <div className="error">
          <h2>Error: {error}</h2>
          <button onClick={fetchScene}>Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className={`App ${getSceneBgClass(scene)}`}>
      <div className="header">
        <h1>Plot Generator</h1>
        <div className="header-buttons">
          <button
            className="reset-button"
            onClick={() => {
              setShowLoadingScreen(true);
              fetchScene();
            }}
          >
            RESET
          </button>
          <button className="help-button" aria-label="Help" onClick={() => setShowHelp(true)}>HELP</button>
          <button className="load-button" onClick={async () => {
            try {
              const response = await axios.get(`${backendURL}/saves`);
              setSavesList(response.data.saves || []);
              setShowLoadModal(true);
            } catch (err) {
              setError("Failed to fetch saves.");
            }
          }}>
            LOAD
          </button>
          <button className="save-button" onClick={() => {
            const now = new Date();
            const defaultName = now.toLocaleString('en-US', {
              year: 'numeric', month: '2-digit', day: '2-digit',
              hour: '2-digit', minute: '2-digit', second: '2-digit',
              hour12: false
            }).replace(/[/:, ]/g, '-');
            setSaveName(defaultName);
            setShowSaveModal(true);
          }}>
            SAVE
          </button>
        </div>
      </div>

      {scene && (
        <div
          className={`scene scene-fade${sceneVisible ? ' in' : ' out'}`}
          key={sceneKey}
        >
          <div className="scene-info">
            <p><strong>Location:</strong> {scene.scene_id}</p>
            <p><strong>Seed:</strong> {scene.seed}</p>
            <p><strong>Visited Scenes:</strong> {scene.visited_scenes}</p>
          </div>

          <div className="description">
            <h2>Scene Description</h2>
            <TypewriterText text={scene.description} speed={18} />
          </div>

          <div className="characters">
            <h2>Characters</h2>
            {scene.npcs && scene.npcs.length > 0 ? (
              <ul>
                {scene.npcs.map((npc, index) => (
                  <li key={index}>
                    <span
                      className="clickable-text npc"
                      onClick={() => handleChoiceClick(`talk to ${npc.toLowerCase()}`)}
                      tabIndex={0}
                      role="link"
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleChoiceClick(`talk to ${npc.toLowerCase()}`); }}
                    >
                      {npc}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>There are no NPCs here.</p>
            )}
          </div>

          <div className="items">
            <h2>Items</h2>
            {scene.items && scene.items.length > 0 ? (
              <ul>
                {scene.items.map((item, index) => (
                  <li key={index}>
                    <span
                      className="clickable-text item"
                      onClick={() => handleItemClick(item)}
                      tabIndex={0}
                      role="link"
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleItemClick(item); }}
                    >
                      {item}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>There are no items here.</p>
            )}
          </div>

          <div className="inventory">
            <h2>Inventory</h2>
            {scene.inventory && scene.inventory.length > 0 ? (
              <ul>
                {scene.inventory.map((item, index) => (
                  <li
                    key={item}
                    className={`inventory-item${item === newlyAddedItem ? ' newly-added' : ''}`}
                  >
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p>Your inventory is empty.</p>
            )}
          </div>

          <div className="choices">
            <h2>Available Actions</h2>
            {scene.choices && scene.choices.length > 0 ? (
              <ul>
                {scene.choices.map((choice, index) => (
                  <li key={index}>
                    <span
                      className="clickable-text choice"
                      onClick={() => handleChoiceClick(choice)}
                      tabIndex={0}
                      role="link"
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleChoiceClick(choice); }}
                    >
                      {choice}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No actions available.</p>
            )}
          </div>
        </div>
      )}

      {scene && scene.current_conversation && (
        <div className="conversation">
          <h3>Talking to: {scene.current_conversation}</h3>
          <div className="conversation-input">
            <form onSubmit={handleCommandSubmit}>
              <input
                type="text"
                value={conversationText}
                onChange={handleConversationChange}
                placeholder="Type your response..."
              />
            </form>
            <div className="conversation-hints">
              <p><em>Try: "quest", "trade", "info", or just chat naturally</em></p>
              <p><em>Say "bye" to end the conversation</em></p>
            </div>
          </div>
        </div>
      )}

      <div className="command-section">
        <form onSubmit={handleCommandSubmit} style={{ position: 'relative' }}>
          <div className="command-line">
            <span className="command-prompt">adventure@terminal:~$</span>
            <input
              type="text"
              value={command}
              onChange={handleCommandChange}
              placeholder={scene && scene.current_conversation ? "In conversation - use chat box above" : "enter command..."}
              disabled={scene && scene.current_conversation}
              onKeyDown={handleCommandKeyDown}
              autoComplete="off"
            />
          </div>
          {autocompleteOptions.length > 0 && (
            <ul className="autocomplete-dropdown">
              {autocompleteOptions.map((opt, idx) => (
                <li
                  key={opt}
                  className={idx === autocompleteIndex ? 'selected' : ''}
                  onMouseDown={() => {
                    setCommand(opt);
                    setAutocompleteOptions([]);
                    setAutocompleteIndex(-1);
                  }}
                >
                  {opt}
                </li>
              ))}
            </ul>
          )}
        </form>
      </div>

      {result && (
        <div className="result">
          <h3>Result:</h3>
          <p>{result}</p>
        </div>
      )}
      {showHelp && (
        <div className="help-modal" onClick={() => setShowHelp(false)}>
          <div className="help-modal-content" onClick={e => e.stopPropagation()}>
            <h2>Help & Tips</h2>
            <ul>
              <li>Type commands like <b>n</b>, <b>take torch</b>, <b>talk to hermit</b></li>
              <li>Use arrow keys for command history</li>
              <li>Click actions or type them in the terminal</li>
              <li>Say <b>bye</b> to end a conversation</li>
              <li>Press <b>Tab</b> for autocomplete</li>
            </ul>
            <button onClick={() => setShowHelp(false)}>Close</button>
          </div>
        </div>
      )}

      {showLoadModal && (
        <div className="help-modal" onClick={() => setShowLoadModal(false)}>
          <div className="help-modal-content" onClick={e => e.stopPropagation()}>
            <h2>Load Game</h2>
            {savesList.length === 0 ? (
              <p>No saves found.</p>
            ) : (
              <ul>
                {savesList.map((filename) => {
                  const match = filename.match(/save_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.json/);
                  const label = match
                    ? new Date(match[1].replace(/_/g, ' ').replace(/-/g, ':').replace(' ', 'T')).toLocaleString()
                    : filename;
                  return (
                    <li key={filename}>
                      <button
                        className="load-save-button"
                        onClick={async () => {
                          try {
                            await axios.post(`${backendURL}/load`, { filename });
                            setShowLoadModal(false);
                            setMessage(`Loaded: ${label}`);
                            fetchScene();
                          } catch (err) {
                            setError("Failed to load save.");
                          }
                        }}
                      >
                        {label}
                      </button>
                    </li>
                  );
                })}
             </ul>
           )}
           <button onClick={() => setShowLoadModal(false)}>Cancel</button>
         </div>
        </div>
      )}

      {showSaveModal && (
        <div className="help-modal" onClick={() => setShowSaveModal(false)}>
          <div className="help-modal-content" onClick={e => e.stopPropagation()}>
            <h2>Save Game</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await axios.post(`${backendURL}/save`, { filename: `save_${saveName}.json` });
                  setShowSaveModal(false);
                  setMessage(`Game saved as: ${saveName}`);
                } catch (err) {
                  setError("Failed to save game.");
                }}}>
              <label>Save Name:
                <input
                  type="text"
                  value={saveName}
                  onChange={e => setSaveName(e.target.value)}
                  style={{ width: '100%', marginTop: 8, marginBottom: 16 }}
                />
              </label>
              <button type="submit" className="save-button">Save</button>
              <button type="button" onClick={() => setShowSaveModal(false)} style={{ marginLeft: 12 }}>
                Cancel
              </button>
          </form>
          </div>
        </div>
      )}

      {message && (
        <div className="message">
          <p>{message}</p>
        </div>
      )}
      <div className="watermark">
        Made by Aahad Vakani. V0.1.2.
      </div>
    </div>
  );
}

export default App;
