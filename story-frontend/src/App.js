import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [scene, setScene] = useState(null);
  const [command, setCommand] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    startNewRunAndFetchScene();
  }, []);

  const fetchScene = async () => {
    setLoading(true);
    try {
      const response = await axios.get('https://interactive-story-o8z0.onrender.com/scene');
      console.log("Fetch Scene API Response:", response.data);
      
      // Check if the response contains an error
      if (response.data.error) {
        setError(response.data.error);
      } else {
        // The API returns the scene data directly, not wrapped in a status/data structure
        setScene(response.data);
        setError(null);
      }
    } catch (error) {
      console.error('Error fetching scene:', error);
      setError(error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const startNewRun = async () => {
    console.log("Starting new run...");
    try {
      const response = await axios.post('https://interactive-story-o8z0.onrender.com/start_new_run');
      console.log("Start New Run API Response:", response.data);
      setMessage(response.data.message);
      return response;
    } catch (error) {
      console.error("Error starting new run:", error);
      setError(error.response?.data?.detail || error.message);
      return null;
    }
  };

  const startNewRunAndFetchScene = async () => {
    setLoading(true);
    const newRunResponse = await startNewRun();
    if (newRunResponse && newRunResponse.status === 200) {
      await fetchScene();
    } else {
      setError("Failed to start new run.");
      setLoading(false);
    }
  };

  const handleCommandSubmit = async (event) => {
    event.preventDefault();
    if (!command.trim()) return;
    
    try {
      const response = await axios.post('https://interactive-story-o8z0.onrender.com/command', { command });
      console.log("Command API Response:", response.data);
      
      // The command endpoint returns { result: "..." }
      setResult(response.data.result || 'Command processed');
      setCommand('');
      
      // Refresh the scene after command
      setTimeout(() => {
        fetchScene();
      }, 500);
      
    } catch (error) {
      console.error('Error submitting command:', error);
      setError(error.response?.data?.detail || error.message);
    }
  };

  const handleCommandChange = (event) => {
    setCommand(event.target.value);
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading your adventure...</div>
      </div>
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

  return (
    <div className="App">
      <div className="header">
        <h1>The Dark Forest Adventure</h1>
        <button className="reset-button" onClick={startNewRunAndFetchScene}>
          RESET
        </button>
      </div>
      
      {scene && (
        <div className="scene">
          <div className="scene-info">
            <p><strong>Location:</strong> {scene.scene_id}</p>
            <p><strong>Seed:</strong> {scene.seed}</p>
            <p><strong>Visited Scenes:</strong> {scene.visited_scenes}</p>
          </div>

          <div className="description">
            <h2>Scene Description</h2>
            <p>{scene.description}</p>
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
                  <li key={index}>{item}</li>
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

      <div className="command-section">
        <form onSubmit={handleCommandSubmit}>
          <div className="command-line">
            <span className="command-prompt">adventure@terminal:~$</span>
            <input
              type="text"
              value={command}
              onChange={handleCommandChange}
              placeholder="enter command..."
            />
          </div>
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
    </div>
  );
}

export default App;