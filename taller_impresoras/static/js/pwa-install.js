/* ============================================================
 * SGMegaPrintLab — Registro del Service Worker + Instalación PWA
 * JS vanilla, sin dependencias. Incluido en base.html.
 * ------------------------------------------------------------
 * 1) Registra /static/sw.js (scope raíz para cubrir toda la app).
 * 2) Captura beforeinstallprompt y muestra el botón
 *    "Instalar Aplicación en este dispositivo" en el Dashboard.
 * 3) Ofrece instrucciones manuales si el navegador no dispara
 *    el evento (p. ej. Firefox o navegación privada).
 * ============================================================ */
(function () {
  'use strict';

  /* ---------- 1. Registro del Service Worker ---------- */
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker
        .register('/static/sw.js', { scope: '/' })
        .then(function (reg) {
          console.info('[PWA] Service Worker registrado, scope:', reg.scope);

          // Actualización automática: cuando un nuevo SW espere, activarlo.
          reg.addEventListener('updatefound', function () {
            var newWorker = reg.installing;
            if (!newWorker) return;
            newWorker.addEventListener('statechange', function () {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                console.info('[PWA] Nueva versión disponible — actualizando caché.');
                newWorker.postMessage('SKIP_WAITING');
              }
            });
          });
        })
        .catch(function (err) {
          console.warn('[PWA] No se pudo registrar el Service Worker:', err);
        });
    });
  }

  /* ---------- 2. Lógica de instalación (beforeinstallprompt) ---------- */
  var deferredPrompt = null;

  function isStandalone() {
    return (
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true || // iOS Safari
      document.referrer.startsWith('android-app://')
    );
  }

  function buildInstallButton() {
    var btn = document.createElement('button');
    btn.id = 'pwaInstallBtn';
    btn.type = 'button';
    btn.className = 'btn btn-primary pwa-install-btn';
    btn.innerHTML =
      '<i class="bi bi-download" aria-hidden="true"></i> ' +
      'Instalar Aplicación en este dispositivo';
    btn.addEventListener('click', function () {
      triggerInstall();
    });
    return btn;
  }

  function showInstallButton() {
    if (isStandalone()) return; // ya instalada: nada que ofrecer
    var mount =
      document.getElementById('pwaInstallMount') ||
      document.querySelector('.container-fluid h1.mb-4');
    if (!mount) return;

    if (document.getElementById('pwaInstallBtn')) return;

    var btn = buildInstallButton();
    if (mount.id === 'pwaInstallMount') {
      mount.appendChild(btn);
    } else {
      // Insertar justo debajo del título del Dashboard.
      mount.insertAdjacentElement('afterend', btn);
    }
  }

  function hideInstallButton(success) {
    var btn = document.getElementById('pwaInstallBtn');
    if (!btn) return;
    if (success) {
      btn.className = 'btn btn-success pwa-install-btn';
      btn.innerHTML = '<i class="bi bi-check-lg" aria-hidden="true"></i> Aplicación instalada';
      btn.disabled = true;
      setTimeout(function () { btn.remove(); }, 4000);
    } else {
      btn.remove();
    }
  }

  function triggerInstall() {
    if (!deferredPrompt) {
      showManualInstallHelp();
      return;
    }
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function (choice) {
      if (choice.outcome === 'accepted') {
        hideInstallButton(true);
      } else {
        // El usuario lo rechazó: seguir ofreciendo en futuras visitas.
        deferredPrompt = null;
        hideInstallButton(false);
      }
    });
  }

  function showManualInstallHelp() {
    var ua = navigator.userAgent;
    var msg;
    if (/Chrome|Edg|Edge/.test(ua)) {
      msg =
        'Para instalar SGMegaPrintLab:\n\n' +
        '• escritorio: menú ⋮ → "Instalar SGMegaPrintLab…" (o el icono de descarga en la barra de direcciones)\n' +
        '• Android: menú ⋮ → "Añadir a pantalla de inicio"';
    } else {
      msg =
        'Tu navegador no permite instalación automática.\n\n' +
        'Usa el menú del navegador → "Añadir a pantalla de inicio" / "Instalar aplicación".';
    }
    alert(msg);
  }

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault(); // evitamos el prompt nativo; usamos nuestro botón
    deferredPrompt = e;
    showInstallButton();
    console.info('[PWA] beforeinstallprompt capturado — botón de instalación visible.');
  });

  window.addEventListener('appinstalled', function () {
    deferredPrompt = null;
    hideInstallButton(true);
    console.info('[PWA] SGMegaPrintLab instalada correctamente.');
  });

  // Si el usuario vuelve con la app ya instalada, ocultar cualquier botón pendiente.
  window.addEventListener('DOMContentLoaded', function () {
    if (isStandalone()) hideInstallButton(false);
  });

  // El evento puede dispararse tras cargar el DOM del Dashboard.
  // showInstallButton() se llama desde beforeinstallprompt; si el evento
  // ya ocurrió antes (raro), nothing to do.
})();
