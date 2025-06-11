// App.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

// --- TypewriterText Component with Sound ---
function TypewriterText({ text, speed = 20, onDone }) {
  const [displayed, setDisplayed] = useState('');
  const indexRef = useRef(0);
  const typeSound = useRef(null);

  useEffect(() => {
    setDisplayed('');
    indexRef.current = 0;
    if (!text) return;

    // Load sound only once
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

// --- ProgressBar Component ---
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

// --- LoadingScreen Component ---
function LoadingScreen({ progress, loading, onStart }) {
  return (
    <div className={`loading-screen${loading ? ' loading-intense' : ''}`}>
      <div className="crt-overlay"></div>
      <div className="loading-content">
        <h1 className="loading-title">The Dark Forest Adventure</h1>
        <div className="loading-backstory">
          <p>
            In the heart of the ancient woods, shadows twist and secrets linger. 
            You are a lone wanderer, drawn by rumors of a lost artifact and the promise of untold power. 
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

// --- BootScreen Component ---
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

// --- Scene Background Helper ---
function getSceneBgClass(scene) {
  if (!scene) return '';
  if (scene.scene_id.includes('forest')) return 'bg-forest';
  if (scene.scene_id.includes('cave')) return 'bg-cave';
  if (scene.scene_id.includes('village')) return 'bg-village';
  if (scene.scene_id.includes('mountain')) return 'bg-mountain';
  if (scene.scene_id.includes('ruin')) return 'bg-ruins';
  if (scene.scene_id.includes('castle')) return 'bg-castle';
  return '';
}

function App() {
  // --- State ---
  const [scene, setScene] = useState(null);
  const [command, setCommand] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(true);
  const [conversationText, setConversationText] = useState('');
  const [progress, setProgress] = useState(0); // 0 to 100
  const [showLoadingScreen, setShowLoadingScreen] = useState(true);

  // Boot sequence state
  const bootMessages = [
    "Booting up Dark Forest Adventure OS v0.1.2...",
    "Initializing memory banks...",
    "Loading procedural templates...",
    "Establishing connection to story engine...",
    "Generating world seed...",
    "Loading locations, items, and NPCs...",
    "Applying CRT filters...",
    "Ready."
  ];
  const [bootStep, setBootStep] = useState(0);
  const [showBoot, setShowBoot] = useState(true);

  // Scene transition state
  const [sceneKey, setSceneKey] = useState(0); // for transition
  const [sceneVisible, setSceneVisible] = useState(true); // for fade

  // Command history & autocomplete
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [autocompleteOptions, setAutocompleteOptions] = useState([]);
  const [autocompleteIndex, setAutocompleteIndex] = useState(-1);

  // For inventory animation
  const [newlyAddedItem, setNewlyAddedItem] = useState(null);

  const backendURL = process.env.REACT_APP_BACKEND_URL || 'https://interactive-story-o8z0.onrender.com';

  // --- Functions ---
  const fetchScene = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${backendURL}/scene`);
      setSceneVisible(false); // start fade out
      setTimeout(() => {
        // Find new inventory item
        if (scene && response.data && response.data.inventory) {
          const prevInv = scene.inventory || [];
          const newInv = response.data.inventory;
          const added = newInv.find(item => !prevInv.includes(item));
          setNewlyAddedItem(added || null);
          if (added) setTimeout(() => setNewlyAddedItem(null), 1200);
        }
        setScene(response.data);
        setSceneKey((k) => k + 1); // change key to force re-mount
        setSceneVisible(true); // fade in
      }, 300); // match fade duration in CSS
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

  const startNewRun = async () => {
    try {
      const response = await axios.post(`${backendURL}/start_new_run`);
      setMessage(response.data.message);
      return response;
    } catch (error) {
      setError(error.response?.data?.detail || error.message);
      return null;
    }
  };

  const startNewRunAndFetchScene = async () => {
    setLoading(true);
    setProgress(10); // Starting
    const newRunResponse = await startNewRun();
    setProgress(50); // Halfway after new run
    if (newRunResponse && newRunResponse.status === 200) {
      await fetchScene();
      setProgress(100); // Done
    } else {
      setError("Failed to start new run.");
      setLoading(false);
      setProgress(0);
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

  // --- Command Input Handlers ---
  const handleCommandChange = (event) => {
    setCommand(event.target.value);
  };

  const handleCommandKeyDown = (e) => {
    // Command history
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
    // Autocomplete
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

  // --- Effects ---
  useEffect(() => {
    startNewRunAndFetchScene();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (showBoot && bootStep < bootMessages.length) {
      const timeout = setTimeout(() => {
        setBootStep(bootStep + 1);
      }, 700); // Adjust speed as desired
      return () => clearTimeout(timeout);
    } else if (showBoot && bootStep === bootMessages.length) {
      setTimeout(() => setShowBoot(false), 700);
    }
  }, [bootStep, showBoot]);

  // Autocomplete options
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

  // --- Conditional Renders ---
  if (showBoot) {
    return <BootScreen messages={bootMessages} step={bootStep} />;
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
          <button onClick={startNewRunAndFetchScene}>Try Again</button>
        </div>
      </div>
    );
  }

  // --- Main App Render ---
  return (
    <div className={`App ${getSceneBgClass(scene)}`}>
      <div className="header">
        <h1>The Dark Forest Adventure</h1>
        <button className="reset-button" onClick={startNewRunAndFetchScene}>
          RESET
        </button>
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
                  <li key={index}>{npc}</li>
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
                  <li key={index}>{item}</li>
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
                  <li key={index}>{choice}</li>
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
            <input
              type="text"
              value={conversationText}
              onChange={handleConversationChange}
              placeholder="Type your response..."
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleCommandSubmit(e);
                }
              }}
            />
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
