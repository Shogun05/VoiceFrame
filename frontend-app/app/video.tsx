import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  SafeAreaView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Platform,
} from "react-native";
import { VideoView, useVideoPlayer } from "expo-video";
import { useRouter, useLocalSearchParams } from "expo-router";
import { ArrowLeft, Share as ShareIcon, Download } from "lucide-react-native";
import { useTheme } from "@/contexts/ThemeContext";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { Toast } from "@/components/Toast";
import { FadingBorderButton } from "@/components/FadingBorderButton";

//  Expo-managed native modules (must install via `expo install`)
import * as FileSystem from "expo-file-system";
import * as Sharing from "expo-sharing";

export default function VideoScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const { prompt } = useLocalSearchParams<{ prompt: string }>();

  const [toast, setToast] = useState({
    visible: false,
    message: "",
    type: "success" as "success" | "error" | "warning",
  });
  const [progressSteps, setProgressSteps] = useState<{step: string, status: 'active' | 'completed' | 'error'}[]>([]);
  const [generationDone, setGenerationDone] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const showToast = (message: string, type: "success" | "error" | "warning") => {
    setToast({ visible: true, message, type });
  };
  const hideToast = () => setToast((prev) => ({ ...prev, visible: false }));

  // 🎥 Video player hook
  const player = useVideoPlayer(videoUrl ? { uri: videoUrl } : undefined, (p) => {
    if (videoUrl) {
      p.loop = true;
      p.play();
    }
  });

  // Track loading state from player
  useEffect(() => {
    if (!player) return;
    const sub = player.addListener("statusUpdate", (status) => {
      setIsLoading(!status.isLoaded);
    });
    return () => sub.remove();
  }, [player]);

  // 🔌 WebSocket connection with prompt handling
  useEffect(() => {
    if (!prompt) {
      showToast("No prompt provided", "error");
      return;
    }

    const WS_URL =
      Platform.OS === "android"
        ? "ws://10.0.2.2:8000/ws/progress" // Android Emulator
        : "ws://localhost:8000/ws/progress"; // Web / iOS

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("WebSocket connected:", WS_URL);
      setWsConnected(true);
      // Don't send prompt immediately - wait for backend's "Waiting for prompt..." message
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received WebSocket message:", data);

        if (data.status === "Waiting for prompt...") {
          // Backend is ready for the prompt - send it now
          console.log("Backend ready, sending prompt:", prompt);
          ws.send(JSON.stringify({ prompt: prompt }));
          
          // Add initial progress step
          setProgressSteps([{ step: "Connecting to server...", status: 'completed' }]);
          
        } else if (data.status === "done") {
          // Mark current step as completed
          setProgressSteps((prev) => 
            prev.map((step, index) => 
              index === prev.length - 1 ? { ...step, status: 'completed' } : step
            )
          );
          
          setGenerationDone(true);
          
          // Construct video URL based on video_id from backend
          const baseUrl = Platform.OS === "android" 
            ? "http://10.0.2.2:8000" 
            : "http://localhost:8000";
          
          const generatedVideoUrl = data.video_id 
            ? `${baseUrl}/video/${data.video_id}`
            : `${baseUrl}/video/latest`; // fallback
          
          setVideoUrl(generatedVideoUrl);
          showToast("Video generation completed!", "success");
          
        } else if (data.status === "error") {
          showToast(data.message || "Video generation failed", "error");
          
          // Mark current step as error and add error step
          setProgressSteps((prev) => {
            const newSteps = [...prev];
            if (newSteps.length > 0) {
              newSteps[newSteps.length - 1] = { ...newSteps[newSteps.length - 1], status: 'error' };
            }
            return [...newSteps, { step: `Error: ${data.message}`, status: 'error' }];
          });
          
        } else {
          // Mark ALL previous steps as completed and add new active step
          setProgressSteps((prev) => {
            const completedSteps = prev.map(step => ({ ...step, status: 'completed' as const }));
            return [...completedSteps, { step: data.status, status: 'active' as const }];
          });
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
        showToast("Error parsing server response", "error");
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      showToast("Connection error - check if backend is running", "error");
      setWsConnected(false);
    };

    ws.onclose = (event) => {
      console.log("WebSocket disconnected:", event.code, event.reason);
      setWsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [prompt]);

  // 📥 Download video
  const handleDownload = async () => {
    if (!videoUrl) {
      showToast("No video available to download", "error");
      return;
    }

    try {
      if (Platform.OS === "web") {
        const link = document.createElement("a");
        link.href = videoUrl;
        link.download = "generated_video.mp4";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        const fileUri = FileSystem.documentDirectory + "generated_video.mp4";
        const { uri } = await FileSystem.downloadAsync(videoUrl, fileUri);
        showToast("Video downloaded to app storage", "success");
        console.log("Video saved to:", uri);
      }
    } catch (error) {
      console.error("Download error:", error);
      showToast("Download failed", "error");
    }
  };

  // 📤 Share video
  const handleShare = async () => {
    if (!videoUrl) {
      showToast("No video available to share", "error");
      return;
    }

    try {
      if (Platform.OS === "web") {
        if (navigator.share) {
          await navigator.share({
            title: "Generated Video",
            text: "Check out this video!",
            url: videoUrl,
          });
        } else {
          showToast("Web Share API not supported", "warning");
        }
      } else {
        const fileUri = FileSystem.documentDirectory + "generated_video.mp4";
        await FileSystem.downloadAsync(videoUrl, fileUri);

        if (!(await Sharing.isAvailableAsync())) {
          showToast("Sharing not available", "warning");
          return;
        }

        await Sharing.shareAsync(fileUri);
      }
    } catch (error) {
      console.error("Share error:", error);
      showToast("Sharing failed", "error");
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <Toast
        message={toast.message}
        type={toast.type}
        visible={toast.visible}
        onHide={hideToast}
      />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={[styles.headerButton, { backgroundColor: theme.surface }]}
        >
          <ArrowLeft size={24} color={theme.text} />
        </TouchableOpacity>

        <Text style={[styles.headerTitle, { color: theme.text }]}>
          Your Generated Video
        </Text>

        <View style={styles.headerActions}>
          <TouchableOpacity
            onPress={handleDownload}
            style={[styles.headerButton, { backgroundColor: theme.surface }]}
          >
            <Download size={22} color={theme.text} />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleShare}
            style={[styles.headerButton, { backgroundColor: theme.surface }]}
          >
            <ShareIcon size={22} color={theme.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Progress / Video */}
      {!generationDone ? (
        <View style={styles.progressContainer}>
          <Text style={[styles.progressTitle, { color: theme.text }]}>
            Video Generation Progress
          </Text>
          
          {/* Connection Status */}
          <View style={styles.connectionStatus}>
            <View style={[
              styles.statusDot, 
              { backgroundColor: wsConnected ? '#4CAF50' : '#F44336' }
            ]} />
            <Text style={[styles.statusText, { color: theme.text }]}>
              {wsConnected ? 'Connected to server' : 'Connecting...'}
            </Text>
          </View>

          {/* Prompt Display */}
          {prompt && (
            <View style={styles.promptContainer}>
              <Text style={[styles.promptText, { color: theme.text }]}>
                Generating video for: <Text style={{ color: theme.primary, fontWeight: '600' }}>{prompt}</Text>
              </Text>
            </View>
          )}
          
          <View style={styles.progressStepsContainer}>
            {progressSteps.map((item, index) => {
              const getStatusColors = () => {
                if (item.status === 'completed') {
                  return { glowColor: '#4CAF50', statusIcon: '✓' };
                } else if (item.status === 'error') {
                  return { glowColor: '#F44336', statusIcon: '✗' };
                } else {
                  return { glowColor: '#2196F3', statusIcon: '•' };
                }
              };
              
              const { glowColor, statusIcon } = getStatusColors();
              
                  return (
                    <View key={index} style={styles.progressStepRow}>
                      <FadingBorderButton
                        title={item.step} // Just the step text, no status icon
                        onPress={() => {}} // No action needed for progress cards
                        disabled={true} // Always disabled since it's just a progress indicator
                        glowColor={glowColor}
                        backgroundColor="transparent" // No background, just border
                        textColor={theme.text}
                        width={320}
                        height={55}
                        style={styles.progressCard}
                        textStyle={{
                          ...styles.progressCardText,
                          opacity: item.status === 'completed' ? 0.9 : 1,
                          fontWeight: item.status === 'active' ? '700' : '500',
                          paddingLeft: item.status === 'completed' ? 30 : 15, // Make room for tick icon
                        }}
                      />
                      
                      {/* Custom status icon overlay */}
                      <View style={styles.statusIconContainer}>
                        {item.status === 'completed' ? (
                          <View style={styles.completedIconContainer}>
                            <Text style={styles.completedIconText}>✓</Text>
                          </View>
                        ) : item.status === 'error' ? (
                          <View style={[styles.errorIcon, { backgroundColor: glowColor }]}>
                            <Text style={styles.errorIconText}>✗</Text>
                          </View>
                        ) : (
                          <View style={[styles.activeIcon, { backgroundColor: glowColor }]}>
                            <Text style={styles.activeIconText}>•</Text>
                          </View>
                        )}
                      </View>
                      
                      {/* Activity indicator for active steps */}
                      {item.status === 'active' && (
                        <View style={styles.activityIndicatorContainer}>
                          <ActivityIndicator 
                            size="small" 
                            color={glowColor}
                            style={styles.activityIndicator}
                          />
                        </View>
                      )}
                    </View>
              );
            })}
          </View>
        </View>
      ) : (
        <View style={styles.videoContainer}>
          {player && videoUrl && (
            <VideoView
              style={styles.video}
              player={player}
              allowsFullscreen
              allowsPictureInPicture
              onLoadStart={() => setIsLoading(true)}
              onError={(e) => {
                console.error("Video error:", e.nativeEvent);
                showToast("Error loading video", "error");
              }}
              onLoad={() => {
                console.log("Video loaded!");
                setIsLoading(false);
              }}
            />
          )}
          {isLoading && (
            <View style={styles.loadingOverlay}>
              <LoadingIndicator />
              <Text style={[styles.loadingText, { color: theme.text }]}>
                Loading video...
              </Text>
            </View>
          )}
        </View>
      )}
    </SafeAreaView>
  );
}

// Styles
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 16,
    paddingTop: 48,
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    flex: 1,
    textAlign: "center",
    marginHorizontal: 16,
  },
  progressContainer: { flex: 1, justifyContent: "center", padding: 20 },
  progressTitle: { fontSize: 22, fontWeight: "bold", marginBottom: 20, textAlign: "center" },
  connectionStatus: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: "500",
  },
  promptContainer: {
    backgroundColor: "rgba(255,255,255,0.1)",
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  promptLabel: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
    opacity: 0.8,
  },
  promptText: {
    fontSize: 16,
    fontWeight: "500",
    lineHeight: 24,
  },
  progressStepsContainer: {
    marginTop: 16,
    paddingHorizontal: 10,
  },
  progressStepRow: {
    marginVertical: 8,
    alignItems: "center",
    position: "relative",
  },
  progressCard: {
    alignSelf: "center",
  },
  progressCardText: {
    fontSize: 15,
    textAlign: "left",
  },
  statusIconContainer: {
    position: "absolute",
    left: 40, // Move closer to text, not at the very edge
    top: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 20,
  },
  completedIconContainer: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "#4CAF50",
    justifyContent: "center",
    alignItems: "center",
  },
  completedIconText: {
    color: "white",
    fontSize: 16,
    fontWeight: "bold",
  },
  errorIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  errorIconText: {
    color: "white",
    fontSize: 16,
    fontWeight: "bold",
  },
  activeIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  activeIconText: {
    color: "white",
    fontSize: 20,
    fontWeight: "bold",
  },
  activityIndicatorContainer: {
    position: "absolute",
    right: 20,
    top: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
  },
  activityIndicator: {
    marginLeft: 8,
  },
  videoContainer: {
    flex: 1,
    margin: 16,
    borderRadius: 16,
    overflow: "hidden",
    backgroundColor: "#000000",
    position: "relative",
  },
  video: { flex: 1 },
  loadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.7)",
  },
  loadingText: { marginTop: 16, fontSize: 16, fontWeight: "600" },
});
