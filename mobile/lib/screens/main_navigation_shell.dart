import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import 'history/history_screen.dart';
import 'home/home_screen.dart';
import 'settings/settings_screen.dart';
import 'upload/upload_screen.dart';

/// Top-level navigation shell providing persistent bottom navigation
/// across Dashboard, Analyze, History, and Settings.
class MainNavigationShell extends StatefulWidget {
  final int initialIndex;

  const MainNavigationShell({super.key, this.initialIndex = 0});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  late int _selectedIndex;

  final List<Widget> _pages = const [
    HomeScreen(),
    UploadScreen(),
    HistoryScreen(),
    SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _selectedIndex = widget.initialIndex;
  }

  void _onDestinationSelected(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: _onDestinationSelected,
        backgroundColor: Colors.white,
        elevation: 8,
        indicatorColor: AppColors.primaryContainer,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard, color: AppColors.primaryDark),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.document_scanner_outlined),
            selectedIcon:
                Icon(Icons.document_scanner, color: AppColors.primaryDark),
            label: 'Analyze',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined),
            selectedIcon: Icon(Icons.history, color: AppColors.primaryDark),
            label: 'History',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings, color: AppColors.primaryDark),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}
