import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [scene, setScene] = useState(null);
  const [command, setCommand] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(''); // New error state

  useEffect(() => {
    fetchScene();
  }, []);

  const fetchScene = async () => {
    try {
      const response = await axios.get('http://localhost:8000/scene'); // Assuming your FastAPI server is running on port 8000
      setScene(response.data);
      setError(''); // Clear any previous errors
    } catch (error) {
      console.error('Error fetching scene:', error);
      setError('Failed to load scene. Please try again later.');
    }
  };

  const handleCommandChange = (event) => {
    setCommand(event.target.value);
  };

  const handleCommandSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('http://localhost:8000/command', { command });
      setScene(response.data);
      setMessage(response.data.message || '');
      setCommand('');
      fetchScene(); // Refetch the scene after submitting the command
      setError(''); // Clear any previous errors
    } catch (error) {
      console.error('Error submitting command:', error);
      setError('Failed to submit command. Please try again.');
    }
  };

  if (!scene) {
    return <div>Loading...</div>;
  }

  return (
    <div className="App">
      <h1>The Dark Forest Adventure</h1>
      {scene && (
        <div className="scene">
          <p>{scene.description}</p>
          <h2>Items</h2>
          <ul>
            {scene.items?.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
          <h2>Inventory</h2>
           <ul>
            {scene.inventory?.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
          <h2>Flags</h2>
           <ul>
            {scene.flags?.map((flag, index) => (
              <li key={index}>{flag}</li>
            ))}
          </ul>
          <h2>Choices</h2>
           <ul>
            {scene.choices?.map((choice, index) => (
              <li key={index}>{choice}</li>
            ))}
          </ul>
        </div>
      )}
      <form onSubmit={handleCommandSubmit}>
        <input
          type="text"
          value={command}
          onChange={handleCommandChange}
          placeholder="Enter command"
        />
        <button type="submit">Submit</button>
      </form>
      {message && <div className="message">{message}</div>}
      {error && <div className="error">{error}</div>}
    </div>
  );
}

export default App;
