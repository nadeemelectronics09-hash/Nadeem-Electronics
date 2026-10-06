import 'dart:async';
import 'dart:typed_data';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:url_launcher/url_launcher.dart';

const _siteUrl = 'https://nadeemelectronics.pythonanywhere.com/';
const _siteHost = 'nadeemelectronics.pythonanywhere.com';
const _navy = Color(0xFF10233F);
const _blue = Color(0xFF1769E0);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const NadeemElectronicsApp());
}

class NadeemElectronicsApp extends StatelessWidget {
  const NadeemElectronicsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Nadeem Electronics',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: _blue),
        scaffoldBackgroundColor: Colors.white,
        useMaterial3: true,
      ),
      home: const StoreWebView(),
    );
  }
}

class StoreWebView extends StatefulWidget {
  const StoreWebView({super.key});

  @override
  State<StoreWebView> createState() => _StoreWebViewState();
}

class _StoreWebViewState extends State<StoreWebView> {
  final _webViewKey = GlobalKey();
  final _connectivity = Connectivity();
  final _dio = Dio();
  InAppWebViewController? _webViewController;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;
  bool _isLoading = true;
  bool _hasLoadedPage = false;
  bool _isOffline = false;
  int _progress = 0;

  @override
  void initState() {
    super.initState();
    _connectivitySubscription =
        _connectivity.onConnectivityChanged.listen(_onConnectivityChanged);
    _connectivity.checkConnectivity().then(
      _onConnectivityChanged,
      onError: (Object error, StackTrace stackTrace) {
        debugPrint('Could not check network connectivity: $error');
      },
    );
  }

  @override
  void dispose() {
    _connectivitySubscription?.cancel();
    _dio.close();
    super.dispose();
  }

  void _onConnectivityChanged(List<ConnectivityResult> results) {
    if (!mounted) return;
    final hasNetwork = results.any(
      (result) => result != ConnectivityResult.none,
    );
    if (!hasNetwork) {
      setState(() => _isOffline = true);
    } else if (_isOffline) {
      setState(() => _isOffline = false);
      unawaited(_loadWebsite());
    }
  }

  Future<void> _loadWebsite() async {
    final controller = _webViewController;
    if (controller == null) return;

    setState(() {
      _isOffline = false;
      _isLoading = true;
      _progress = 0;
    });
    await controller.loadUrl(
      urlRequest: URLRequest(url: WebUri(_siteUrl)),
    );
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  bool _isStoreUrl(Uri uri) =>
      uri.scheme == 'https' && uri.host.toLowerCase() == _siteHost;

  Future<void> _openExternal(Uri uri) async {
    try {
      final opened = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
      if (!opened) {
        _showMessage('Could not open this link: ${uri.toString()}');
      }
    } on PlatformException catch (error) {
      _showMessage('Could not open this link: ${error.message ?? error.code}');
    }
  }

  Future<void> _downloadFile(
    InAppWebViewController controller,
    DownloadStartRequest request,
  ) async {
    final uri = Uri.tryParse(request.url.toString());
    if (uri == null || !_isStoreUrl(uri)) {
      _showMessage('This download link is not from the store website.');
      return;
    }

    try {
      var downloadUri = uri;
      Response<List<int>>? response;
      for (var redirectCount = 0; redirectCount <= 5; redirectCount++) {
        final cookies = await CookieManager.instance().getCookies(
          url: WebUri(downloadUri.toString()),
          webViewController: controller,
        );
        final cookieHeader = cookies
            .map((cookie) => '${cookie.name}=${cookie.value}')
            .join('; ');
        final headers = <String, String>{};
        if (cookieHeader.isNotEmpty) headers['Cookie'] = cookieHeader;
        if (request.userAgent != null && request.userAgent!.isNotEmpty) {
          headers['User-Agent'] = request.userAgent!;
        }

        final downloadResponse = await _dio.get<List<int>>(
          downloadUri.toString(),
          options: Options(
            followRedirects: false,
            headers: headers,
            responseType: ResponseType.bytes,
            validateStatus: (status) => status != null && status < 400,
          ),
        );
        final status = downloadResponse.statusCode;
        if (status != null && status >= 300 && status < 400) {
          final location = downloadResponse.headers.value('location');
          final nextUri =
              location == null ? null : downloadUri.resolve(location);
          if (nextUri == null || !_isStoreUrl(nextUri)) {
            _showMessage('This download redirected outside the store website.');
            return;
          }
          if (redirectCount == 5) {
            _showMessage('The download redirected too many times.');
            return;
          }
          downloadUri = nextUri;
          continue;
        }
        response = downloadResponse;
        break;
      }

      final data = response?.data;
      if (data == null || data.isEmpty) {
        _showMessage('The website returned an empty download.');
        return;
      }

      final suggestedName = request.suggestedFilename?.trim();
      final pathName = downloadUri.pathSegments.isNotEmpty
          ? downloadUri.pathSegments.last
          : '';
      final safeName = (suggestedName?.isNotEmpty == true
              ? suggestedName!
              : pathName.isNotEmpty
                  ? pathName
                  : 'nadeem-electronics-download')
          .replaceAll(RegExp(r'[\\/:*?"<>|]'), '_');
      final extensionStart = safeName.lastIndexOf('.');
      final extension =
          extensionStart > 0 ? safeName.substring(extensionStart + 1) : '';
      final fileName =
          extensionStart > 0 ? safeName.substring(0, extensionStart) : safeName;

      final savedPath = await FileSaver.instance.saveAs(
        name: fileName,
        bytes: Uint8List.fromList(data),
        fileExtension: extension,
        mimeType: MimeType.custom,
        customMimeType: request.mimeType ?? 'application/octet-stream',
        dialogTitle: 'Save download',
      );
      if (savedPath != null) {
        _showMessage('Download saved successfully.');
      }
    } on DioException catch (error) {
      _showMessage('Download failed: ${error.message ?? 'network error'}');
    } on PlatformException catch (error) {
      _showMessage('Could not save the download: ${error.message ?? error.code}');
    }
  }

  Future<void> _handleBack() async {
    final controller = _webViewController;
    if (controller != null && await controller.canGoBack()) {
      await controller.goBack();
      return;
    }
    await SystemNavigator.pop();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope<Object?>(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) unawaited(_handleBack());
      },
      child: Scaffold(
        body: SafeArea(
          child: Stack(
            children: [
              InAppWebView(
                key: _webViewKey,
                initialUrlRequest: URLRequest(url: WebUri(_siteUrl)),
                initialSettings: InAppWebViewSettings(
                  javaScriptEnabled: true,
                  domStorageEnabled: true,
                  supportZoom: true,
                  useShouldOverrideUrlLoading: true,
                  useOnDownloadStart: true,
                  supportMultipleWindows: true,
                  javaScriptCanOpenWindowsAutomatically: false,
                  mediaPlaybackRequiresUserGesture: true,
                  safeBrowsingEnabled: true,
                ),
                onWebViewCreated: (controller) {
                  _webViewController = controller;
                },
                onLoadStart: (controller, url) {
                  if (!mounted) return;
                  setState(() {
                    _isLoading = true;
                    _progress = 0;
                    _isOffline = false;
                  });
                },
                onProgressChanged: (controller, progress) {
                  if (!mounted) return;
                  setState(() => _progress = progress);
                },
                onLoadStop: (controller, url) {
                  if (!mounted) return;
                  setState(() {
                    _isLoading = false;
                    _hasLoadedPage = true;
                    _progress = 100;
                    _isOffline = false;
                  });
                },
                onReceivedError: (controller, request, error) {
                  if (request.isForMainFrame == true && mounted) {
                    setState(() {
                      _isLoading = false;
                      _isOffline = true;
                    });
                  }
                },
                onShouldOverrideUrlLoading: (controller, action) async {
                  final webUri = action.request.url;
                  if (webUri == null) return NavigationActionPolicy.CANCEL;
                  final uri = Uri.tryParse(webUri.toString());
                  if (uri == null) return NavigationActionPolicy.CANCEL;
                  if (_isStoreUrl(uri)) return NavigationActionPolicy.ALLOW;

                  if (uri.host.toLowerCase() == _siteHost &&
                      uri.scheme == 'http') {
                    await controller.loadUrl(
                      urlRequest: URLRequest(
                        url: WebUri(uri.replace(scheme: 'https').toString()),
                      ),
                    );
                  } else {
                    await _openExternal(uri);
                  }
                  return NavigationActionPolicy.CANCEL;
                },
                onCreateWindow: (controller, action) async {
                  final webUri = action.request.url;
                  final uri =
                      webUri == null ? null : Uri.tryParse(webUri.toString());
                  if (uri != null) {
                    if (_isStoreUrl(uri)) {
                      await controller.loadUrl(
                        urlRequest: URLRequest(url: WebUri(uri.toString())),
                      );
                    } else {
                      await _openExternal(uri);
                    }
                  }
                  return true;
                },
                onShowFileChooser: (controller, request) async {
                  return ShowFileChooserResponse(handledByClient: false);
                },
                onDownloadStartRequest: (controller, request) {
                  unawaited(_downloadFile(controller, request));
                },
              ),
              if (_isLoading && _hasLoadedPage && !_isOffline)
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  child: LinearProgressIndicator(
                    value: _progress == 0 ? null : _progress / 100,
                    minHeight: 3,
                    color: _blue,
                    backgroundColor: const Color(0xFFE8EEF6),
                  ),
                ),
              if (_isLoading && !_hasLoadedPage && !_isOffline)
                const Positioned.fill(child: _LoadingScreen()),
              if (_isOffline)
                Positioned.fill(
                  child: _OfflineScreen(onRetry: () => unawaited(_loadWebsite())),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LoadingScreen extends StatelessWidget {
  const _LoadingScreen();

  @override
  Widget build(BuildContext context) {
    return const ColoredBox(
      color: Colors.white,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _StoreMark(size: 76),
            SizedBox(height: 22),
            Text(
              'Nadeem Electronics',
              style: TextStyle(
                color: _navy,
                fontSize: 21,
                fontWeight: FontWeight.w700,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Loading your store',
              style: TextStyle(color: Color(0xFF66758A), fontSize: 14),
            ),
            SizedBox(height: 24),
            SizedBox(
              width: 30,
              height: 30,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: _blue,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OfflineScreen extends StatelessWidget {
  const _OfflineScreen({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: Colors.white,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.wifi_off_rounded,
                color: _blue,
                size: 66,
              ),
              const SizedBox(height: 22),
              const Text(
                'No Internet Connection',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _navy,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Check your internet connection, then try again.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Color(0xFF66758A),
                  fontSize: 15,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Try again'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StoreMark extends StatelessWidget {
  const _StoreMark({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: _navy,
        borderRadius: BorderRadius.circular(size * 0.27),
      ),
      child: Icon(
        Icons.electrical_services_rounded,
        color: Colors.white,
        size: size * 0.61,
      ),
    );
  }
}
