import { useState, useRef } from 'react'
import { Search, Upload, FileText, Image, Globe, Brain, Loader2, Download, Settings, Info } from 'lucide-react'
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
  const fileInputRef = useRef(null)

  const API_BASE = 'http://localhost:5000/api/v1'

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

      const data = await response.json()
      
      clearInterval(progressInterval)
      setSearchProgress(100)
      
      setTimeout(() => {
        setSearchResults(data)
        setIsSearching(false)
        setSearchProgress(0)
      }, 500)

    } catch (error) {
      console.error('Errore nella ricerca:', error)
      clearInterval(progressInterval)
      setSearchResults({
        success: false,
        error: 'Errore di connessione al server'
      })
      setIsSearching(false)
      setSearchProgress(0)
    }
  }

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return

    setIsUploading(true)

    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${API_BASE}/upload`, {
          method: 'POST',
          body: formData
        })

        const data = await response.json()
        
        if (data.success) {
          setUploadedFiles(prev => [...prev, {
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'success',
            message: data.message
          }])
        } else {
          setUploadedFiles(prev => [...prev, {
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'error',
            message: data.error
          }])
        }

      } catch (error) {
        console.error('Errore upload:', error)
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'error',
          message: 'Errore di connessione'
        }])
      }
    }

    setIsUploading(false)
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getAgentIcon = (agentName) => {
    switch (agentName) {
      case 'text': return <FileText className="w-4 h-4" />
      case 'image': return <Image className="w-4 h-4" />
      case 'web': return <Globe className="w-4 h-4" />
      case 'document': return <FileText className="w-4 h-4" />
      case 'synthesis': return <Brain className="w-4 h-4" />
      default: return <Search className="w-4 h-4" />
    }
  }

  const getAgentColor = (agentName) => {
    switch (agentName) {
      case 'text': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
      case 'image': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'web': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
      case 'document': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300'
      case 'synthesis': return 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 sticky top-0 z-50">
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
                <p className="text-sm text-muted-foreground">Ricerca Intelligente Multi-Modale</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Impostazioni
              </Button>
              <Button variant="outline" size="sm">
                <Info className="w-4 h-4 mr-2" />
                Info
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
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
              <FileText className="w-4 h-4" />
              <span>Risultati</span>
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search" className="space-y-6">
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm dark:bg-slate-800/70">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Search className="w-5 h-5" />
                  <span>Ricerca Intelligente</span>
                </CardTitle>
                <CardDescription>
                  Inserisci la tua query per cercare attraverso testo, immagini, documenti e web
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex space-x-2">
                  <Textarea
                    placeholder="Inserisci la tua query di ricerca..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="min-h-[100px] resize-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        handleSearch()
                      }
                    }}
                  />
                </div>
                
                {isSearching && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span>Ricerca in corso...</span>
                      <span>{searchProgress}%</span>
                    </div>
                    <Progress value={searchProgress} className="w-full" />
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <div className="flex space-x-2">
                    <Badge variant="outline" className="flex items-center space-x-1">
                      <FileText className="w-3 h-3" />
                      <span>Testo</span>
                    </Badge>
                    <Badge variant="outline" className="flex items-center space-x-1">
                      <Image className="w-3 h-3" />
                      <span>Immagini</span>
                    </Badge>
                    <Badge variant="outline" className="flex items-center space-x-1">
                      <Globe className="w-3 h-3" />
                      <span>Web</span>
                    </Badge>
                    <Badge variant="outline" className="flex items-center space-x-1">
                      <Brain className="w-3 h-3" />
                      <span>AI Synthesis</span>
                    </Badge>
                  </div>
                  
                  <Button 
                    onClick={handleSearch} 
                    disabled={!query.trim() || isSearching}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                  >
                    {isSearching ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4 mr-2" />
                    )}
                    Cerca
                  </Button>
                </div>

                <div className="text-xs text-muted-foreground">
                  Suggerimento: Premi Ctrl+Enter per cercare rapidamente
                </div>
              </CardContent>
            </Card>

            {/* Quick Examples */}
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm dark:bg-slate-800/70">
              <CardHeader>
                <CardTitle className="text-lg">Esempi di Ricerca</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Ricerca Testuale</h4>
                    <div className="space-y-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="justify-start h-auto p-2 text-left"
                        onClick={() => setQuery("Cos'è l'intelligenza artificiale?")}
                      >
                        "Cos'è l'intelligenza artificiale?"
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="justify-start h-auto p-2 text-left"
                        onClick={() => setQuery("Ultime notizie sulla tecnologia")}
                      >
                        "Ultime notizie sulla tecnologia"
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Ricerca Avanzata</h4>
                    <div className="space-y-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="justify-start h-auto p-2 text-left"
                        onClick={() => setQuery("Analizza i documenti caricati per trovare informazioni sui contratti")}
                      >
                        "Analizza documenti per contratti"
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="justify-start h-auto p-2 text-left"
                        onClick={() => setQuery("Trova immagini simili a quelle caricate")}
                      >
                        "Trova immagini simili"
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm dark:bg-slate-800/70">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Upload className="w-5 h-5" />
                  <span>Carica File nella Knowledge Base</span>
                </CardTitle>
                <CardDescription>
                  Carica documenti, immagini e file per arricchire la knowledge base
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div 
                  className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={(e) => {
                    e.preventDefault()
                    handleFileUpload(Array.from(e.dataTransfer.files))
                  }}
                  onDragOver={(e) => e.preventDefault()}
                >
                  <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">Trascina file qui o clicca per selezionare</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Supportati: PDF, DOCX, TXT, XLSX, PPTX, JPG, PNG, GIF
                  </p>
                  <Button variant="outline">
                    Seleziona File
                  </Button>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  accept=".pdf,.docx,.txt,.xlsx,.pptx,.jpg,.jpeg,.png,.gif,.bmp"
                  onChange={(e) => handleFileUpload(Array.from(e.target.files || []))}
                />

                {isUploading && (
                  <Alert>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <AlertDescription>
                      Caricamento file in corso...
                    </AlertDescription>
                  </Alert>
                )}

                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium">File Caricati</h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {uploadedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className={`w-2 h-2 rounded-full ${
                              file.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                            }`} />
                            <div>
                              <p className="font-medium text-sm">{file.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {formatFileSize(file.size)} • {file.message}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results" className="space-y-6">
            {searchResults ? (
              searchResults.success ? (
                <div className="space-y-6">
                  {/* Search Summary */}
                  <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm dark:bg-slate-800/70">
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Risultati per: "{searchResults.query}"</span>
                        <Badge variant="outline">
                          {searchResults.total_results} risultati in {searchResults.processing_time?.toFixed(2)}s
                        </Badge>
                      </CardTitle>
                      <CardDescription>
                        Agenti utilizzati: {searchResults.agents_used?.map(agent => (
                          <Badge key={agent} className={`ml-1 ${getAgentColor(agent)}`}>
                            {getAgentIcon(agent)}
                            <span className="ml-1">{agent}</span>
                          </Badge>
                        ))}
                      </CardDescription>
                    </CardHeader>
                  </Card>

                  {/* Results by Agent */}
                  {Object.entries(searchResults.results || {}).map(([agentName, agentResults]) => (
                    agentResults.results && agentResults.results.length > 0 && (
                      <Card key={agentName} className="shadow-lg border-0 bg-white/70 backdrop-blur-sm dark:bg-slate-800/70">
                        <CardHeader>
                          <CardTitle className="flex items-center space-x-2">
                            {getAgentIcon(agentName)}
                            <span className="capitalize">{agentName} Agent</span>
                            <Badge className={getAgentColor(agentName)}>
                              {agentResults.results.length} risultati
                            </Badge>
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {agentResults.results.map((result, index) => (
                            <div key={index} className="border rounded-lg p-4 hover:bg-muted/50 transition-colors">
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-medium text-lg">{result.title}</h4>
                                <Badge variant="outline" className="ml-2">
                                  Score: {(result.relevance_score * 100).toFixed(0)}%
                                </Badge>
                              </div>
                              
                              {result.summary && (
                                <p className="text-muted-foreground mb-3 leading-relaxed">
                                  {result.summary}
                                </p>
                              )}
                              
                              {result.source_url && (
                                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                                  <Globe className="w-3 h-3" />
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
                              
                              <div className="flex items-center justify-between mt-3">
                                <Badge variant="secondary" className="text-xs">
                                  {result.source_type}
                                </Badge>
                                <Button variant="ghost" size="sm">
                                  <Download className="w-3 h-3 mr-1" />
                                  Dettagli
                                </Button>
                              </div>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )
                  ))}
                </div>
              ) : (
                <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
                  <AlertDescription className="text-red-800 dark:text-red-200">
                    Errore nella ricerca: {searchResults.error}
                  </AlertDescription>
                </Alert>
              )
            ) : (
              <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm dark:bg-slate-800/70">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Search className="w-16 h-16 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">Nessun risultato disponibile</h3>
                  <p className="text-muted-foreground text-center">
                    Esegui una ricerca per visualizzare i risultati qui
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              © 2024 Deep Search AI - Ricerca Intelligente Multi-Modale
            </p>
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <span>Powered by GPT-5</span>
              <Separator orientation="vertical" className="h-4" />
              <span>Multi-Agent Architecture</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
