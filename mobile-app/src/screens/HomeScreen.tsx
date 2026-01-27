import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useQuery } from 'react-query';

import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import VoiceButton from '../components/VoiceButton';
import PriceCard from '../components/PriceCard';
import AlertCard from '../components/AlertCard';
import WeatherCard from '../components/WeatherCard';
import { apiService } from '../services/apiService';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const { colors } = useTheme();
  const [refreshing, setRefreshing] = useState(false);

  // Fetch dashboard data
  const { data: dashboardData, refetch } = useQuery(
    'dashboard',
    () => apiService.getDashboardData(),
    {
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const quickActions = [
    {
      id: 'prices',
      title: 'मंडी भाव',
      subtitle: 'आज के भाव देखें',
      icon: 'trending-up',
      color: colors.primary,
    },
    {
      id: 'weather',
      title: 'मौसम',
      subtitle: 'मौसम की जानकारी',
      icon: 'wb-sunny',
      color: colors.warning,
    },
    {
      id: 'crop-planning',
      title: 'फसल योजना',
      subtitle: 'फसल की सलाह',
      icon: 'eco',
      color: colors.success,
    },
    {
      id: 'alerts',
      title: 'अलर्ट',
      subtitle: 'महत्वपूर्ण सूचनाएं',
      icon: 'notifications',
      color: colors.error,
    },
  ];

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Welcome Section */}
        <View style={[styles.welcomeSection, { backgroundColor: colors.primary }]}>
          <Text style={styles.welcomeText}>
            नमस्ते {user?.name}! 🙏
          </Text>
          <Text style={styles.welcomeSubtext}>
            आज आपके लिए क्या कर सकते हैं?
          </Text>
        </View>

        {/* Voice Interface */}
        <View style={styles.voiceSection}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            आवाज़ से पूछें
          </Text>
          <View style={styles.voiceContainer}>
            <VoiceButton />
            <Text style={[styles.voiceHint, { color: colors.textSecondary }]}>
              "आज गेहूं का भाव क्या है?" पूछें
            </Text>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActionsSection}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            त्वरित कार्य
          </Text>
          <View style={styles.quickActionsGrid}>
            {quickActions.map((action) => (
              <TouchableOpacity
                key={action.id}
                style={[styles.quickActionCard, { backgroundColor: colors.surface }]}
                activeOpacity={0.7}
              >
                <View style={[styles.quickActionIcon, { backgroundColor: action.color + '20' }]}>
                  <Icon name={action.icon} size={24} color={action.color} />
                </View>
                <Text style={[styles.quickActionTitle, { color: colors.text }]}>
                  {action.title}
                </Text>
                <Text style={[styles.quickActionSubtitle, { color: colors.textSecondary }]}>
                  {action.subtitle}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Recent Prices */}
        <View style={styles.pricesSection}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              आज के भाव
            </Text>
            <TouchableOpacity>
              <Text style={[styles.seeAllText, { color: colors.primary }]}>
                सभी देखें
              </Text>
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.priceCardsContainer}>
              <PriceCard
                commodity="गेहूं"
                price="₹2,200"
                change="+50"
                changePercent="+2.3%"
                location="दिल्ली मंडी"
              />
              <PriceCard
                commodity="चावल"
                price="₹3,500"
                change="-25"
                changePercent="-0.7%"
                location="पंजाब मंडी"
              />
              <PriceCard
                commodity="मक्का"
                price="₹1,800"
                change="+75"
                changePercent="+4.3%"
                location="उत्तर प्रदेश मंडी"
              />
            </View>
          </ScrollView>
        </View>

        {/* Alerts */}
        <View style={styles.alertsSection}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            महत्वपूर्ण सूचनाएं
          </Text>
          <AlertCard
            type="warning"
            title="मौसम चेतावनी"
            message="अगले 3 दिनों में बारिश की संभावना है"
            time="2 घंटे पहले"
          />
          <AlertCard
            type="success"
            title="MSP अपडेट"
            message="गेहूं का न्यूनतम समर्थन मूल्य बढ़ाया गया"
            time="5 घंटे पहले"
          />
        </View>

        {/* Weather */}
        <View style={styles.weatherSection}>
          <WeatherCard />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  welcomeSection: {
    padding: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 5,
  },
  welcomeSubtext: {
    fontSize: 16,
    color: '#ffffff',
    opacity: 0.9,
  },
  voiceSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 15,
  },
  voiceContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  voiceHint: {
    fontSize: 14,
    marginTop: 10,
    textAlign: 'center',
  },
  quickActionsSection: {
    padding: 20,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionCard: {
    width: (width - 60) / 2,
    padding: 15,
    borderRadius: 12,
    marginBottom: 15,
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  quickActionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
    textAlign: 'center',
  },
  quickActionSubtitle: {
    fontSize: 12,
    textAlign: 'center',
  },
  pricesSection: {
    padding: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '500',
  },
  priceCardsContainer: {
    flexDirection: 'row',
    paddingRight: 20,
  },
  alertsSection: {
    padding: 20,
  },
  weatherSection: {
    padding: 20,
    paddingBottom: 30,
  },
});