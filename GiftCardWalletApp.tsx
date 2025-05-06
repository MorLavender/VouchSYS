import React, { useState, useRef } from 'react';
import { Camera, Plus, X, CreditCard, Eye, EyeOff } from 'lucide-react';

const GiftCardWalletApp = () => {
  const [cards, setCards] = useState([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [newCardDetails, setNewCardDetails] = useState({
    name: '',
    number: '',
    balance: '',
    expiryDate: '',
    imageData: null
  });
  const [showCardNumbers, setShowCardNumbers] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const startCamera = async () => {
    setIsCapturing(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      alert("Could not access camera. Please check permissions.");
      setIsCapturing(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsCapturing(false);
  };

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const imageData = canvas.toDataURL('image/jpeg');
      setNewCardDetails({...newCardDetails, imageData});
      stopCamera();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setNewCardDetails({...newCardDetails, imageData: event.target.result});
      };
      reader.readAsDataURL(file);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewCardDetails({...newCardDetails, [name]: value});
  };

  const addCard = (e) => {
    e.preventDefault();
    if (!newCardDetails.name || !newCardDetails.number) {
      alert("Card name and number are required!");
      return;
    }
    
    setCards([...cards, {...newCardDetails, id: Date.now()}]);
    setNewCardDetails({
      name: '',
      number: '',
      balance: '',
      expiryDate: '',
      imageData: null
    });
  };

  const deleteCard = (id) => {
    setCards(cards.filter(card => card.id !== id));
  };

  const toggleCardNumberVisibility = () => {
    setShowCardNumbers(!showCardNumbers);
  };

  const formatCardNumber = (number) => {
    if (!number) return '';
    if (!showCardNumbers) {
      return '•••• •••• •••• ' + number.slice(-4);
    }
    return number.replace(/(\d{4})/g, '$1 ').trim();
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-2xl font-bold">Gift Card Wallet</h1>
      </header>

      <main className="flex-1 p-4">
        {/* Card List */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Your Gift Cards</h2>
            <button 
              onClick={toggleCardNumberVisibility}
              className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
            >
              {showCardNumbers ? <EyeOff size={16} /> : <Eye size={16} />}
              {showCardNumbers ? 'Hide Numbers' : 'Show Numbers'}
            </button>
          </div>

          {cards.length === 0 ? (
            <div className="bg-white rounded-lg p-6 text-center shadow">
              <CreditCard className="mx-auto mb-2 text-gray-400" size={48} />
              <p className="text-gray-500">No gift cards yet. Add your first card below.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {cards.map(card => (
                <div key={card.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                  {card.imageData && (
                    <div className="h-40 overflow-hidden rounded-t-lg">
                      <img 
                        src={card.imageData} 
                        alt={card.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold text-lg">{card.name}</h3>
                      <button 
                        onClick={() => deleteCard(card.id)} 
                        className="text-red-500 hover:text-red-700"
                      >
                        <X size={20} />
                      </button>
                    </div>
                    <p className="text-gray-700 mb-1">Card: {formatCardNumber(card.number)}</p>
                    {card.balance && <p className="text-gray-700 mb-1">Balance: ${card.balance}</p>}
                    {card.expiryDate && <p className="text-gray-700">Expires: {card.expiryDate}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add New Card */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-xl font-semibold mb-4">Add New Gift Card</h2>
          
          {isCapturing ? (
            <div className="mb-4">
              <div className="relative">
                <video 
                  ref={videoRef} 
                  autoPlay
                  className="w-full h-64 object-cover rounded-lg bg-gray-800"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="border-2 border-white border-dashed rounded-lg w-3/4 h-3/4 flex items-center justify-center">
                    <p className="text-white bg-black bg-opacity-50 px-2 py-1 rounded">Center gift card here</p>
                  </div>
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                <button 
                  onClick={captureImage}
                  className="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 flex-1"
                >
                  Capture
                </button>
                <button 
                  onClick={stopCamera}
                  className="bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700"
                >
                  Cancel
                </button>
              </div>
              <canvas ref={canvasRef} className="hidden" />
            </div>
          ) : (
            <div className="mb-4">
              {newCardDetails.imageData ? (
                <div className="relative">
                  <img 
                    src={newCardDetails.imageData} 
                    alt="Card preview" 
                    className="w-full h-48 object-contain rounded-lg border"
                  />
                  <button 
                    onClick={() => setNewCardDetails({...newCardDetails, imageData: null})}
                    className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={startCamera}
                    className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 flex items-center gap-2 flex-1"
                  >
                    <Camera size={20} />
                    Take Photo
                  </button>
                  <button
                    onClick={() => fileInputRef.current.click()}
                    className="bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700 flex items-center gap-2 flex-1"
                  >
                    <Plus size={20} />
                    Upload Image
                  </button>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileUpload}
                    accept="image/*"
                    className="hidden"
                  />
                </div>
              )}
            </div>
          )}

          <form onSubmit={addCard}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-gray-700 mb-1">Gift Card Name*</label>
                <input
                  type="text"
                  name="name"
                  value={newCardDetails.name}
                  onChange={handleInputChange}
                  placeholder="e.g. Amazon, Starbucks"
                  className="w-full p-2 border rounded"
                  required
                />
              </div>
              
              <div>
                <label className="block text-gray-700 mb-1">Card Number*</label>
                <input
                  type="text"
                  name="number"
                  value={newCardDetails.number}
                  onChange={handleInputChange}
                  placeholder="Card number"
                  className="w-full p-2 border rounded"
                  required
                />
              </div>
              
              <div>
                <label className="block text-gray-700 mb-1">Balance (optional)</label>
                <input
                  type="text"
                  name="balance"
                  value={newCardDetails.balance}
                  onChange={handleInputChange}
                  placeholder="e.g. 50.00"
                  className="w-full p-2 border rounded"
                />
              </div>
              
              <div>
                <label className="block text-gray-700 mb-1">Expiry Date (optional)</label>
                <input
                  type="text"
                  name="expiryDate"
                  value={newCardDetails.expiryDate}
                  onChange={handleInputChange}
                  placeholder="MM/YYYY"
                  className="w-full p-2 border rounded"
                />
              </div>
            </div>
            
            <button 
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded font-bold hover:bg-blue-700"
            >
              Add Gift Card to Wallet
            </button>
          </form>
        </div>
      </main>

      <footer className="bg-gray-800 text-white p-4 text-center">
        <p>Gift Card Wallet App &copy; 2025</p>
      </footer>
    </div>
  );
};

export default GiftCardWalletApp;
