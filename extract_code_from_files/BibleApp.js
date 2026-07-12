import React, { useState, useEffect, useRef } from 'react';
import { Book, MessageSquare, Send, Link, ChevronRight, History } from 'lucide-react';

// Navigation Placeholder Component
const NavigationPlaceholder = ({ book, chapter, getBookName, onNavigate }) => {
  const [navigationHistory, setNavigationHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  // Update navigation history only when manually selecting a book or chapter
  // We'll track this separately from cross-reference navigation
  useEffect(() => {
    if (book) {
      // Check if this location is already the last item in history
      const lastItem = navigationHistory[navigationHistory.length - 1];
      if (!lastItem || lastItem.book !== book.abbrev || lastItem.chapter !== chapter) {
        // Add to history, keeping only the last 10 items
        setNavigationHistory(prev => {
          const newHistory = [...prev, { book: book.abbrev, chapter, timestamp: Date.now() }];
          return newHistory.slice(-10); // Keep only last 10 entries
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [book, chapter]); // Intentionally omitting navigationHistory to prevent infinite loops
  
  if (!book) return null;
  
  return (
    <div className="relative">
      {/* Current Location Display */}
      <div className="flex items-center bg-gray-100 px-3 py-1 rounded-md text-gray-700">
        <span>Primary reading:</span>
        <span className="font-medium mx-1">{getBookName(book.abbrev)}</span>
        <ChevronRight className="h-4 w-4 mx-1" />
        <span className="font-medium">Chapter {chapter}</span>
        
        {/* History Button */}
        <button 
          onClick={() => setShowHistory(!showHistory)}
          className="ml-2 p-1 rounded-full hover:bg-gray-200 focus:outline-none"
          title="Navigation history"
        >
          <History className="h-4 w-4" />
        </button>
      </div>
      
      {/* Navigation History Dropdown */}
      {showHistory && navigationHistory.length > 0 && (
        <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-10">
          <div className="p-2 border-b border-gray-200">
            <h3 className="font-medium">Reading History</h3>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {[...navigationHistory].reverse().map((item, index) => (
              <button
                key={index}
                onClick={() => {
                  onNavigate(item.book, item.chapter);
                  setShowHistory(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-gray-100 flex items-center justify-between"
              >
                <span>
                  {getBookName(item.book)} {item.chapter}
                </span>
                <span className="text-xs text-gray-500">
                  {getRelativeTime(item.timestamp)}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to display relative time
const getRelativeTime = (timestamp) => {
  const now = Date.now();
  const diff = now - timestamp;
  
  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
};

// Main component
const BibleApp = () => {
  const [bibleData, setBibleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBook, setSelectedBook] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(1);
  const [userInput, setUserInput] = useState('');
  const [outputText, setOutputText] = useState('');
  const [crossReferences, setCrossReferences] = useState({});
  const [showCrossRef, setShowCrossRef] = useState(null);
  
  // Add a ref for the chapter content container
  const chapterContentRef = useRef(null);
  
  // State to track primary reading vs cross-reference viewing
  const [isViewingCrossRef, setIsViewingCrossRef] = useState(false);
  const [primaryReading, setPrimaryReading] = useState({
    book: null,
    chapter: 1
  });

  // Load Bible data and cross-references on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Load Bible data
        const bibleResponse = await fetch('/en_kjv.json');
        if (!bibleResponse.ok) {
          throw new Error(`HTTP error! Status: ${bibleResponse.status}`);
        }
        const bibleData = await bibleResponse.json();
        setBibleData(bibleData);
        
        // Set default selected book to Genesis (first book)
        if (bibleData && bibleData.length > 0) {
          setSelectedBook(bibleData[0]);
          setPrimaryReading({
            book: bibleData[0],
            chapter: 1
          });
        }
        
        // Load cross-references from the JSON file
        await loadCrossReferences();
        
        setLoading(false);
      } catch (err) {
        console.error("Failed to load data:", err);
        setError("Failed to load Bible data. Please try again later.");
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  // Load cross references from external JSON file
  const loadCrossReferences = async () => {
    try {
      console.log("Attempting to load cross references from /crossRefs.json");
      const response = await fetch('/crossRefs.json');
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      // Log the response text for debugging if needed
      const responseText = await response.text();
      console.log("Response received, first 50 characters:", responseText.substring(0, 50));
      
      // Check if the response starts with HTML tags (indicating we got a webpage instead of JSON)
      if (responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html')) {
        throw new Error("Received HTML instead of JSON. The crossRefs.json file may not exist in the correct location.");
      }
      
      // Parse the JSON (after confirming it's not HTML)
      const crossRefs = JSON.parse(responseText);
      setCrossReferences(crossRefs);
      console.log("Cross references loaded successfully");
      return crossRefs;
    } catch (err) {
      console.error("Failed to load cross references:", err);
      
      // Provide more specific error message based on the type of error
      let errorMessage = "Cross-references could not be loaded. Some features may be limited.";
      
      if (err.message.includes("HTML instead of JSON")) {
        errorMessage = "The cross-reference file was not found. Check that crossRefs.json is in the public folder.";
      } else if (err instanceof SyntaxError) {
        errorMessage = "The cross-reference file contains invalid JSON. Please check the file format.";
      }
      
      setError(errorMessage);
      
      // Attempt to continue with the Bible app despite the error
      // Wait 5 seconds and then clear the error so the user can still use the app
      setTimeout(() => {
        setError(null);
        // Now set empty cross references to allow the app to function
        setCrossReferences({});
      }, 5000);
      
      return {};
    }
  };

  // Handle book selection
  const handleBookSelect = (abbrev) => {
    if (bibleData) {
      const book = bibleData.find(b => b.abbrev === abbrev);
      setSelectedBook(book);
      setSelectedChapter(1); // Reset to first chapter when book changes
      setShowCrossRef(null); // Hide any cross-reference popup
      
      // Update primary reading
      setPrimaryReading({
        book: book,
        chapter: 1
      });
      setIsViewingCrossRef(false);
      
      // Scroll to top when book changes
      if (chapterContentRef.current) {
        chapterContentRef.current.scrollTop = 0;
      }
    }
  };
  
  // Handle chapter selection
  const handleChapterSelect = (chapterNum) => {
    setSelectedChapter(chapterNum);
    setShowCrossRef(null); // Hide any cross-reference popup
    
    // Update primary reading
    if (selectedBook) {
      setPrimaryReading({
        book: selectedBook,
        chapter: chapterNum
      });
      setIsViewingCrossRef(false);
    }
    
    // Scroll to top when chapter changes
    if (chapterContentRef.current) {
      chapterContentRef.current.scrollTop = 0;
    }
  };
  
  // Handle user input submission
  const handleSubmit = () => {
    // Future Ollama integration will go here
    setOutputText(`You asked: ${userInput}\n\nThis is where the Ollama response will appear.`);
    
    // Keep the input for now - you might want to clear it in a real app
    // setUserInput('');
  };

  // Handle click on a verse to navigate to a cross-reference
  const handleCrossRefNavigate = (ref) => {
    // Find the book in the Bible data
    const book = bibleData.find(b => b.abbrev === ref.book);
    if (book) {
      setSelectedBook(book);
      setSelectedChapter(ref.chapter);
      
      // Mark that we're viewing a cross-reference (not primary reading)
      setIsViewingCrossRef(true);
      
      // Hide the cross-reference popup
      setShowCrossRef(null);
      
      // Add a slight delay before scrolling to the verse
      setTimeout(() => {
        const verseElement = document.getElementById(`verse-${ref.verse}`);
        if (verseElement && chapterContentRef.current) {
          verseElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          
          // Highlight the verse temporarily
          verseElement.classList.add('bg-yellow-100');
          setTimeout(() => {
            verseElement.classList.remove('bg-yellow-100');
          }, 3000); // Remove highlight after 3 seconds
        }
      }, 300);
    }
  };

  // If still loading
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <div className="text-2xl font-bold mb-4">Loading Bible Data...</div>
          <div className="animate-pulse bg-blue-500 h-2 w-64 rounded"></div>
        </div>
      </div>
    );
  }
  
  // If there was an error
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-red-100">
        <div className="text-center text-red-600">
          <div className="text-2xl font-bold mb-4">Error</div>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  // Helper function to get book name based on abbreviation
  const getBookName = (abbrev) => {
    const bookNames = {
      'gn': 'Genesis', 'ex': 'Exodus', 'lv': 'Leviticus', 'nm': 'Numbers', 'dt': 'Deuteronomy',
      'js': 'Joshua', 'jud': 'Judges', 'rt': 'Ruth', '1sm': '1 Samuel', '2sm': '2 Samuel',
      '1kgs': '1 Kings', '2kgs': '2 Kings', '1ch': '1 Chronicles', '2ch': '2 Chronicles',
      'ezr': 'Ezra', 'ne': 'Nehemiah', 'et': 'Esther', 'job': 'Job', 'ps': 'Psalms',
      'prv': 'Proverbs', 'ec': 'Ecclesiastes', 'so': 'Song of Solomon', 'is': 'Isaiah',
      'jr': 'Jeremiah', 'lm': 'Lamentations', 'ez': 'Ezekiel', 'dn': 'Daniel',
      'ho': 'Hosea', 'jl': 'Joel', 'am': 'Amos', 'ob': 'Obadiah', 'jn': 'Jonah',
      'mi': 'Micah', 'na': 'Nahum', 'hk': 'Habakkuk', 'zp': 'Zephaniah', 'hg': 'Haggai',
      'zc': 'Zechariah', 'ml': 'Malachi', 'mt': 'Matthew', 'mk': 'Mark', 'lk': 'Luke',
      'jo': 'John', 'act': 'Acts', 'rm': 'Romans', '1co': '1 Corinthians', '2co': '2 Corinthians',
      'gl': 'Galatians', 'eph': 'Ephesians', 'ph': 'Philippians', 'cl': 'Colossians',
      '1ts': '1 Thessalonians', '2ts': '2 Thessalonians', '1tm': '1 Timothy', '2tm': '2 Timothy',
      'tt': 'Titus', 'phm': 'Philemon', 'hb': 'Hebrews', 'jm': 'James', '1pe': '1 Peter',
      '2pe': '2 Peter', '1jo': '1 John', '2jo': '2 John', '3jo': '3 John', 'jd': 'Jude',
      're': 'Revelation'
    };
    
    return bookNames[abbrev] || abbrev;
  };

  // Main render
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Book Selection Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold flex items-center">
            <Book className="mr-2 h-5 w-5" />
            Bible Books
          </h2>
        </div>
        <div className="overflow-y-auto h-full">
          {bibleData && bibleData.map(book => (
            <button
              key={book.abbrev}
              onClick={() => handleBookSelect(book.abbrev)}
              className={`w-full text-left px-4 py-2 hover:bg-gray-100 ${
                selectedBook && selectedBook.abbrev === book.abbrev ? 'bg-blue-100 font-medium' : ''
              }`}
            >
              {getBookName(book.abbrev)}
            </button>
          ))}
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar with Navigation and Chapter Selection */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold">
                {selectedBook ? getBookName(selectedBook.abbrev) : 'Select a Book'}
              </h1>
              
              {selectedBook && (
                <div className="flex items-center ml-4">
                  <span className="mr-2">Chapter:</span>
                  <select 
                    value={selectedChapter}
                    onChange={(e) => handleChapterSelect(parseInt(e.target.value))}
                    className="border border-gray-300 rounded px-2 py-1"
                  >
                    {selectedBook.chapters.map((_, index) => (
                      <option key={index + 1} value={index + 1}>
                        {index + 1}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            
            {/* Navigation History / Breadcrumb */}
            <div className="flex items-center space-x-2">
              <NavigationPlaceholder 
                book={primaryReading.book} 
                chapter={primaryReading.chapter}
                getBookName={getBookName}
                onNavigate={(book, chapter) => {
                  if (book && bibleData) {
                    const bookObj = bibleData.find(b => b.abbrev === book);
                    if (bookObj) {
                      setSelectedBook(bookObj);
                      setSelectedChapter(chapter);
                      setPrimaryReading({
                        book: bookObj,
                        chapter: chapter
                      });
                      setIsViewingCrossRef(false);
                      if (chapterContentRef.current) {
                        chapterContentRef.current.scrollTop = 0;
                      }
                    }
                  }
                }}
              />
              
              {/* Return to Primary Reading button (only when viewing cross-reference) */}
              {isViewingCrossRef && (
                <button
                  onClick={() => {
                    if (primaryReading.book) {
                      setSelectedBook(primaryReading.book);
                      setSelectedChapter(primaryReading.chapter);
                      setIsViewingCrossRef(false);
                      if (chapterContentRef.current) {
                        chapterContentRef.current.scrollTop = 0;
                      }
                    }
                  }}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                >
                  Return to Primary Reading
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Bible Text and AI Interaction Split View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Bible Text Display */}
          <div ref={chapterContentRef} className="flex-1 overflow-y-auto p-6 bg-white relative">
            {selectedBook && selectedChapter > 0 && (
              <div>
                <h2 className="text-xl mr-2 font-semibold mb-4">
                  {getBookName(selectedBook.abbrev)} {selectedChapter}
                </h2>
                <div className="space-y-2">
                  {selectedBook.chapters[selectedChapter - 1].map((verse, index) => {
                    const verseNumber = index + 1;
                    const refKey = `${selectedBook.abbrev}-${selectedChapter}-${verseNumber}`;
                    const hasReference = crossReferences[refKey] && crossReferences[refKey].length > 0;
                    
                    return (
                      <div 
                        key={index} 
                        id={`verse-${verseNumber}`}
                        className={`leading-relaxed p-2 rounded-md transition-colors ${
                          hasReference ? 'hover:bg-blue-50' : ''
                        }`}
                      >
                        <p className="flex">
                          <span className="font-bold text-blue-600 mr-2">{verseNumber}</span>
                          <span className="flex-1">{verse}</span>
                          
                          {hasReference && (
                            <button
                              onClick={() => setShowCrossRef(showCrossRef === refKey ? null : refKey)}
                              className="ml-2 text-blue-500 hover:text-blue-700 focus:outline-none"
                              title="Show cross-references"
                            >
                              <Link className="h-4 w-4" />
                            </button>
                          )}
                        </p>
                        
                        {/* Cross-reference popup */}
                        {showCrossRef === refKey && (
                          <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md shadow-sm">
                            <h4 className="font-medium mb-2">Cross References:</h4>
                            <ul className="space-y-2">
                              {crossReferences[refKey].map((ref, i) => (
                                <li key={i} className="text-sm">
                                  <button 
                                    onClick={() => handleCrossRefNavigate(ref)}
                                    className="text-blue-600 hover:text-blue-800 font-medium"
                                  >
                                    {getBookName(ref.book)} {ref.chapter}:{ref.verse}
                                  </button>
                                  <p className="text-gray-700 mt-1">{ref.text}</p>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {/* Chapter Navigation - Simple inline approach */}
                <div className="mt-8 flex justify-between pb-4">
                  {selectedChapter > 1 ? (
                    <button 
                      onClick={() => handleChapterSelect(selectedChapter - 1)}
                      className="bg-white bg-opacity-80 border border-gray-300 hover:bg-gray-100 text-gray-700 font-bold rounded px-4 py-2 shadow"
                    >
                      &lt; Previous Chapter
                    </button>
                  ) : (
                    <div></div>
                  )}
                  
                  {selectedBook && selectedChapter < selectedBook.chapters.length && (
                    <button 
                      onClick={() => handleChapterSelect(selectedChapter + 1)}
                      className="bg-white bg-opacity-80 border border-gray-300 hover:bg-gray-100 text-gray-700 font-bold rounded px-4 py-2 shadow"
                    >
                      Next Chapter &gt;
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
          
          {/* AI Interaction Panel */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold flex items-center">
                <MessageSquare className="mr-2 h-5 w-5" />
                Ask about Scripture
              </h2>
            </div>
            
            {/* Output Display */}
            <div className="flex-1 p-4 overflow-y-auto bg-white">
              {outputText ? (
                <div className="whitespace-pre-wrap">{outputText}</div>
              ) : (
                <div className="text-gray-500 italic">
                  Ask a question about the Bible text to see the response here.
                </div>
              )}
            </div>
            
            {/* Input Area */}
            <div className="p-4 border-t border-gray-200">
              <div className="flex items-start">
                <textarea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="Type your question here..."
                  className="flex-1 border border-gray-300 rounded-l px-3 py-2 min-h-24 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSubmit}
                  className="bg-blue-600 text-white px-4 py-2 rounded-r hover:bg-blue-700 transition-colors h-24 flex items-center justify-center"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BibleApp;