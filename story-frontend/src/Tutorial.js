// Tutorial.js
import React, { useState } from 'react';
import './App.css';

const CLASSES = [
  { name: "Wanderer", desc: "Balanced stats, good at exploring." },
  { name: "Mystic", desc: "High magic, low strength." },
  { name: "Warrior", desc: "High strength, low magic." },
  { name: "Rogue", desc: "Stealthy and quick." }
];

export default function Tutorial({ onComplete }) {
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
              >
                Enter the World
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
