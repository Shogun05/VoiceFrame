import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { BookOpen, Clock, Play } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';

export default function StoriesScreen() {
  const { theme } = useTheme();

  const mockStories = [
    {
      id: '1',
      title: 'A Journey Through the Stars',
      preview: 'In a distant galaxy, a young explorer discovers...',
      duration: '2:34',
      createdAt: '2 hours ago',
    },
    {
      id: '2',
      title: 'The Magic Forest',
      preview: 'Once upon a time, in an enchanted forest...',
      duration: '1:45',
      createdAt: '1 day ago',
    },
  ];

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>My Stories</Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          Your generated video stories
        </Text>
      </View>

      <ScrollView style={styles.scrollView}>
        {mockStories.length > 0 ? (
          mockStories.map((story) => (
            <TouchableOpacity
              key={story.id}
              style={[styles.storyCard, { backgroundColor: theme.surface }]}
            >
              <View style={styles.storyHeader}>
                <BookOpen size={20} color={theme.primary} />
                <Text style={[styles.storyTitle, { color: theme.text }]}>
                  {story.title}
                </Text>
              </View>
              
              <Text style={[styles.storyPreview, { color: theme.textSecondary }]}>
                {story.preview}
              </Text>
              
              <View style={styles.storyFooter}>
                <View style={styles.storyMeta}>
                  <Clock size={16} color={theme.textSecondary} />
                  <Text style={[styles.metaText, { color: theme.textSecondary }]}>
                    {story.duration}
                  </Text>
                  <Text style={[styles.metaText, { color: theme.textSecondary }]}>
                    • {story.createdAt}
                  </Text>
                </View>
                
                <TouchableOpacity style={[styles.playButton, { backgroundColor: theme.primary }]}>
                  <Play size={16} color="#FFFFFF" />
                </TouchableOpacity>
              </View>
            </TouchableOpacity>
          ))
        ) : (
          <View style={styles.emptyState}>
            <BookOpen size={64} color={theme.textSecondary} />
            <Text style={[styles.emptyTitle, { color: theme.text }]}>
              No Stories Yet
            </Text>
            <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
              Create your first story from the Home tab
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 24,
    paddingVertical: 24,
    paddingTop: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  storyCard: {
    padding: 20,
    marginVertical: 8,
    borderRadius: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  storyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  storyTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginLeft: 8,
    flex: 1,
  },
  storyPreview: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  storyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  storyMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 12,
  },
  playButton: {
    padding: 8,
    borderRadius: 8,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
});