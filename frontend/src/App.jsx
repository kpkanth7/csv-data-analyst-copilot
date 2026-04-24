import { useState } from 'react';
import Upload from './Upload';
import Chat from './Chat';

function App() {
  const [sessionId, setSessionId] = useState(null);

  return (
    <div className="app-container">
      {!sessionId ? (
        <Upload onUploadSuccess={setSessionId} />
      ) : (
        <Chat sessionId={sessionId} />
      )}
    </div>
  );
}

export default App;
