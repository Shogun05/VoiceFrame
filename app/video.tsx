import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  SafeAreaView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  FlatList,
  Platform,
} from "react-native";
import { VideoView, useVideoPlayer } from "expo-video";
import { useRouter } from "expo-router";
import { ArrowLeft, Share as ShareIcon, Download } from "lucide-react-native";
import { useTheme } from "@/contexts/ThemeContext";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { Toast } from "@/components/Toast";

//  Expo-managed native modules (must install via `expo install`)
import * as FileSystem from "expo-file-system";
import * as Sharing from "expo-sharing";

export default function VideoScreen() {
  const { theme } = useTheme();
  const router = useRouter();

  const [toast, setToast] = useState({
    visible: false,
    message: "",
    type: "success" as "success" | "error" | "warning",
  });
  const [progressSteps, setProgressSteps] = useState<string[]>([]);
  const [generationDone, setGenerationDone] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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

  // 🔌 WebSocket connection
  useEffect(() => {
    const WS_URL =
      Platform.OS === "android"
        ? "ws://10.0.2.2:8000/ws/progress" // Android Emulator
        : "ws://localhost:8000/ws/progress"; // Web / iOS

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("WebSocket connected:", WS_URL);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.status === "done") {
          setGenerationDone(true);
          setVideoUrl(
            data.video_url ||
              "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
          );
          showToast("Video generation completed!", "success");
        } else {
          setProgressSteps((prev) => [...prev, data.status]);
        }
      } catch (err) {
        console.error("Failed to parse WS message", err);
        showToast("Error parsing progress", "error");
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      showToast("Connection error", "error");
    };

    ws.onclose = () => console.log("WebSocket disconnected");

    return () => ws.close();
  }, []);

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
          <FlatList
            data={progressSteps}
            keyExtractor={(item, idx) => idx.toString()}
            renderItem={({ item }) => (
              <View style={styles.stepRow}>
                <Text style={[styles.stepText, { color: theme.text }]}>{item}</Text>
                <ActivityIndicator size="small" color={theme.primary} style={{ marginLeft: 8 }} />
              </View>
            )}
            style={{ marginTop: 16 }}
          />
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
  stepRow: { flexDirection: "row", alignItems: "center", marginVertical: 8 },
  stepText: { fontSize: 18 },
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
