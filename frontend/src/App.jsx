import { useState, useRef, useEffect } from 'react'
import { Search, Upload, FileText, Image, Globe, Brain, Loader2, Download, Settings, Info, ExternalLink, Github, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState(null)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [activeTab, setActiveTab] = useState('search')
  const [searchProgress, setSearchProgress] = useState(0)
  const [apiStatus, setApiStatus] = useState('checking')
  const fileInputRef = useRef(null)

  // Configurazione API dinamica per deployment
  const API_BASE = import.meta.env.VITE_API_URL || 
                   (import.meta.env.PROD ? 'https://deep-search-ai-api.onrender.com/api/v1' : 'http://localhost:5000/api/v1')

  // Controlla stato API all'avvio
  useEffect(() => {
    checkApiStatus()
  }, [])

  const checkApiStatus = async () => {
    try {
      const response = await fetch(`${API_BASE.replace('/api/v1', '')}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        }
      })
      
      if (response.ok) {
        setApiStatus('online')
      } else {
        setApiStatus('offline')
      }
    } catch (error) {
      console.log('API non disponibile, modalità demo attiva')
      setApiStatus('demo')
    }
  }

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    setSearchProgress(0)
    setSearchResults(null)

    // Simula progresso
    const progressInterval = setInterval(() => {
      setSearchProgress(prev => Math.min(prev + 10, 90))
    }, 200)

    try {
      if (apiStatus === 'demo') {
        // Modalità demo con risultati simulati
        setTimeout(() => {
          clearInterval(progressInterval)
          setSearchProgress(100)
          setSearchResults({
            query: query,
            total_results: 3,
            processing_time: 1.2,
            agents_used: ['text', 'web', 'synthesis'],
            results: [
              {
                id: 1,
                title: "Risultato Demo - Ricerca Testuale",
                content: "Questo è un risultato di esempio per la modalità demo. La ricerca reale richiede una connessione API attiva.",
                summary: "Esempio di ricerca semantica avanzata con AI",
                source_type: "text",
                relevance_score: 0.95,
                confidence_score: 0.88,
                agent_name: "TextAgent",
                created_at: new Date().toISOString()
              },
              {
                id: 2,
                title: "Risultato Demo - Ricerca Web",
                content: "Esempio di risultato da ricerca web intelligente con analisi contenuti.",
                summary: "Ricerca web con crawling e analisi AI",
                source_type: "web",
                source_url: "https://example.com",
                relevance_score: 0.87,
                confidence_score: 0.82,
                agent_name: "WebAgent",
                created_at: new Date().toISOString()
              },
              {
                id: 3,
                title: "Risultato Demo - Sintesi",
                content: "Sintesi intelligente aggregando risultati da multiple fonti con AI.",
                summary: "Aggregazione e sintesi multi-agente",
                source_type: "synthesis",
                relevance_score: 0.92,
                confidence_score: 0.85,
                agent_name: "SynthesisAgent",
                created_at: new Date().toISOString()
              }
            ]
          })
          setIsSearching(false)
        }, 2000)
        return
      }

      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          options: {
            max_results: 10
          }
        })
      })

      clearInterval(progressInterval)
      setSearchProgress(100)

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data)
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Errore nella ricerca')
      }
    } catch (error) {
      console.error('Errore ricerca:', error)
      clearInterval(progressInterval)
      setSearchResults({
        error: error.message || 'Errore di connessione al server'
      })
    } finally {
      setIsSearching(false)
    }
  }

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    const formData = new FormData()

    Array.from(files).forEach(file => {
      formData.append('files', file)
    })

    try {
      if (apiStatus === 'demo') {
        // Modalità demo
        setTimeout(() => {
          const demoFiles = Array.from(files).map((file, index) => ({
            id: Date.now() + index,
            filename: file.name,
            size: file.size,
            type: file.type,
            status: 'processed',
            uploaded_at: new Date().toISOString()
          }))
          setUploadedFiles(prev => [...prev, ...demoFiles])
          setIsUploading(false)
        }, 1500)
        return
      }

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setUploadedFiles(prev => [...prev, ...data.files])
      } else {
        throw new Error('Errore nel caricamento file')
      }
    } catch (error) {
      console.error('Errore upload:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const getAgentBadgeColor = (agentName) => {
    const colors = {
      'TextAgent': 'bg-blue-100 text-blue-800',
      'ImageAgent': 'bg-green-100 text-green-800',
      'DocumentAgent': 'bg-purple-100 text-purple-800',
      'WebAgent': 'bg-orange-100 text-orange-800',
      'SynthesisAgent': 'bg-pink-100 text-pink-800'
    }
    return colors[agentName] || 'bg-gray-100 text-gray-800'
  }

  const getSourceIcon = (sourceType) => {
    const icons = {
      'text': FileText,
      'image': Image,
      'document': FileText,
      'web': Globe,
      'synthesis': Brain
    }
    return icons[sourceType] || FileText
  }

  const exampleQueries = [
    "Analizza le tendenze dell'intelligenza artificiale nel 2024",
    "Trova informazioni sui cambiamenti climatici",
    "Ricerca avanzata su machine learning",
    "Analizza documenti PDF caricati",
    "Estrai testo da immagini"
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Deep Search AI
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Ricerca Intelligente Multi-Modale
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Status API */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  apiStatus === 'online' ? 'bg-green-500' : 
                  apiStatus === 'demo' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  {apiStatus === 'online' ? 'API Online' : 
                   apiStatus === 'demo' ? 'Modalità Demo' : 'API Offline'}
                </span>
              </div>
              
              <Button variant="outline" size="sm" asChild>
                <a href="https://github.com/enzococca/deep-search-ai" target="_blank" rel="noopener noreferrer">
                  <Github className="w-4 h-4 mr-2" />
                  GitHub
                </a>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Ricerca Avanzata con <span className="text-blue-600">Intelligenza Artificiale</span>
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto">
            Utilizza agenti AI specializzati per ricerche multi-modali su testo, immagini, documenti e web. 
            Powered by GPT-5 e tecnologie avanzate di machine learning.
          </p>
        </div>

        {/* Demo Alert */}
        {apiStatus === 'demo' && (
          <Alert className="mb-8 bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800">
            <Zap className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800 dark:text-yellow-200">
              <strong>Modalità Demo Attiva:</strong> L'API backend non è disponibile. 
              Stai visualizzando risultati simulati per esplorare l'interfaccia.
              <a href="https://github.com/enzococca/deep-search-ai" target="_blank" rel="noopener noreferrer" 
                 className="ml-2 inline-flex items-center text-yellow-700 hover:text-yellow-900 dark:text-yellow-300">
                Scarica il codice <ExternalLink className="w-3 h-3 ml-1" />
              </a>
            </AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="search" className="flex items-center space-x-2">
              <Search className="w-4 h-4" />
              <span>Ricerca</span>
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center space-x-2">
              <Upload className="w-4 h-4" />
              <span>Carica File</span>
            </TabsTrigger>
            <TabsTrigger value="results" className="flex items-center space-x-2">
              <Brain className="w-4 h-4" />
              <span>Risultati</span>
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Search className="w-5 h-5" />
                  <span>Ricerca Intelligente</span>
                </CardTitle>
                <CardDescription>
                  Inserisci la tua query per una ricerca multi-modale con AI. 
                  Gli agenti specializzati analizzeranno testo, immagini, documenti e web.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex space-x-2">
                  <Textarea
                    placeholder="Inserisci la tua domanda o query di ricerca..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="min-h-[100px] resize-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSearch()
                      }
                    }}
                  />
                  <Button 
                    onClick={handleSearch} 
                    disabled={isSearching || !query.trim()}
                    className="px-8"
                  >
                    {isSearching ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4" />
                    )}
                  </Button>
                </div>

                {/* Progress Bar */}
                {isSearching && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-slate-600">
                      <span>Ricerca in corso...</span>
                      <span>{searchProgress}%</span>
                    </div>
                    <Progress value={searchProgress} className="w-full" />
                  </div>
                )}

                {/* Example Queries */}
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Esempi di ricerca:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {exampleQueries.map((example, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => setQuery(example)}
                        className="text-xs"
                      >
                        {example}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="text-center">
                <CardContent className="pt-6">
                  <FileText className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                  <h3 className="font-semibold mb-1">Ricerca Testuale</h3>
                  <p className="text-sm text-slate-600">Analisi semantica avanzata</p>
                </CardContent>
              </Card>
              <Card className="text-center">
                <CardContent className="pt-6">
                  <Image className="w-8 h-8 mx-auto mb-2 text-green-600" />
                  <h3 className="font-semibold mb-1">Analisi Immagini</h3>
                  <p className="text-sm text-slate-600">OCR e computer vision</p>
                </CardContent>
              </Card>
              <Card className="text-center">
                <CardContent className="pt-6">
                  <FileText className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                  <h3 className="font-semibold mb-1">Documenti</h3>
                  <p className="text-sm text-slate-600">PDF, DOCX, Excel, PPT</p>
                </CardContent>
              </Card>
              <Card className="text-center">
                <CardContent className="pt-6">
                  <Globe className="w-8 h-8 mx-auto mb-2 text-orange-600" />
                  <h3 className="font-semibold mb-1">Ricerca Web</h3>
                  <p className="text-sm text-slate-600">Crawling intelligente</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Upload className="w-5 h-5" />
                  <span>Carica File</span>
                </CardTitle>
                <CardDescription>
                  Carica documenti, immagini o altri file per aggiungerli alla knowledge base.
                  Supportati: PDF, DOCX, Excel, PowerPoint, immagini.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={(e) => {
                    e.preventDefault()
                    handleFileUpload(e.dataTransfer.files)
                  }}
                  onDragOver={(e) => e.preventDefault()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    accept=".pdf,.docx,.xlsx,.pptx,.jpg,.jpeg,.png,.gif,.txt"
                    onChange={(e) => handleFileUpload(e.target.files)}
                  />
                  {isUploading ? (
                    <div className="space-y-2">
                      <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-600" />
                      <p className="text-slate-600">Caricamento in corso...</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="w-8 h-8 mx-auto text-slate-400" />
                      <p className="text-slate-600">
                        Clicca per selezionare file o trascina qui
                      </p>
                      <p className="text-sm text-slate-500">
                        PDF, DOCX, Excel, PowerPoint, Immagini
                      </p>
                    </div>
                  )}
                </div>

                {/* Uploaded Files */}
                {uploadedFiles.length > 0 && (
                  <div className="mt-6 space-y-2">
                    <h3 className="font-semibold">File Caricati:</h3>
                    {uploadedFiles.map((file) => (
                      <div key={file.id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <FileText className="w-4 h-4 text-slate-600" />
                          <div>
                            <p className="font-medium">{file.filename}</p>
                            <p className="text-sm text-slate-500">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-green-600">
                          {file.status || 'Elaborato'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results" className="space-y-6">
            {searchResults ? (
              searchResults.error ? (
                <Alert className="bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800">
                  <AlertDescription className="text-red-800 dark:text-red-200">
                    <strong>Errore:</strong> {searchResults.error}
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-6">
                  {/* Results Summary */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Risultati per: "{searchResults.query}"</span>
                        <Badge variant="outline">
                          {searchResults.total_results} risultati
                        </Badge>
                      </CardTitle>
                      <CardDescription>
                        Elaborazione completata in {searchResults.processing_time}s • 
                        Agenti utilizzati: {searchResults.agents_used?.join(', ')}
                      </CardDescription>
                    </CardHeader>
                  </Card>

                  {/* Results List */}
                  <div className="space-y-4">
                    {searchResults.results?.map((result) => {
                      const SourceIcon = getSourceIcon(result.source_type)
                      return (
                        <Card key={result.id} className="hover:shadow-md transition-shadow">
                          <CardHeader>
                            <div className="flex items-start justify-between">
                              <div className="flex items-center space-x-2">
                                <SourceIcon className="w-5 h-5 text-slate-600" />
                                <CardTitle className="text-lg">{result.title}</CardTitle>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Badge className={getAgentBadgeColor(result.agent_name)}>
                                  {result.agent_name?.replace('Agent', '')}
                                </Badge>
                                <Badge variant="outline">
                                  {Math.round(result.relevance_score * 100)}%
                                </Badge>
                              </div>
                            </div>
                            {result.summary && (
                              <CardDescription>{result.summary}</CardDescription>
                            )}
                          </CardHeader>
                          <CardContent>
                            <p className="text-slate-700 dark:text-slate-300 mb-4">
                              {result.content}
                            </p>
                            {result.source_url && (
                              <div className="flex items-center space-x-2 text-sm text-blue-600">
                                <ExternalLink className="w-4 h-4" />
                                <a 
                                  href={result.source_url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="hover:underline"
                                >
                                  {result.source_url}
                                </a>
                              </div>
                            )}
                            <div className="flex items-center justify-between mt-4 pt-4 border-t">
                              <div className="text-sm text-slate-500">
                                Confidenza: {Math.round((result.confidence_score || 0) * 100)}%
                              </div>
                              <div className="text-sm text-slate-500">
                                {new Date(result.created_at).toLocaleString('it-IT')}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                  </div>
                </div>
              )
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <Brain className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                  <h3 className="text-lg font-semibold mb-2">Nessun risultato</h3>
                  <p className="text-slate-600">
                    Esegui una ricerca per visualizzare i risultati qui.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <Brain className="w-5 h-5 text-blue-600" />
              <span className="font-semibold">Deep Search AI</span>
              <Badge variant="outline">v1.0.0</Badge>
            </div>
            <div className="flex items-center space-x-4 text-sm text-slate-600">
              <a href="https://github.com/enzococca/deep-search-ai" target="_blank" rel="noopener noreferrer" 
                 className="hover:text-blue-600 flex items-center space-x-1">
                <Github className="w-4 h-4" />
                <span>GitHub</span>
              </a>
              <span>•</span>
              <span>Powered by GPT-5 & OpenAI</span>
              <span>•</span>
              <span>Made with ❤️ in Italy</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
