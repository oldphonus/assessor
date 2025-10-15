#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система мониторинга и анализа системных ресурсов
Отслеживает использование CPU, памяти, диска и сети с уведомлениями
"""

import psutil
import time
import json
import os
from datetime import datetime, timedelta
from collections import deque
import threading
import platform

class SystemMonitor:
    def __init__(self, log_file="system_monitor.json"):
        self.log_file = log_file
        self.monitoring = False
        self.log_data = deque(maxlen=1000)  # Храним последние 1000 записей
        self.alerts = []
        
        # Пороговые значения для уведомлений
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'network_speed': 100  # MB/s
        }
        
        self.load_log_data()
    
    def load_log_data(self):
        """Загружает данные логов из файла"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data[-1000:]:  # Последние 1000 записей
                        self.log_data.append(entry)
        except Exception as e:
            print(f"Ошибка при загрузке логов: {e}")
    
    def save_log_data(self):
        """Сохраняет данные логов в файл"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.log_data), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении логов: {e}")
    
    def get_system_info(self):
        """Получает базовую информацию о системе"""
        try:
            info = {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total': psutil.virtual_memory().total,
                'boot_time': psutil.boot_time()
            }
            return info
        except Exception as e:
            print(f"Ошибка при получении системной информации: {e}")
            return {}
    
    def get_cpu_info(self):
        """Получает информацию о процессоре"""
        try:
            # Общая загрузка CPU
            cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
            
            # Загрузка по ядрам
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Частоты процессора
            cpu_freq = psutil.cpu_freq()
            
            # Загрузка системы (Load Average) - только для Unix-систем
            load_avg = None
            try:
                if hasattr(os, 'getloadavg'):
                    load_avg = os.getloadavg()
            except:
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_per_core': cpu_per_core,
                'cpu_freq_current': cpu_freq.current if cpu_freq else None,
                'cpu_freq_min': cpu_freq.min if cpu_freq else None,
                'cpu_freq_max': cpu_freq.max if cpu_freq else None,
                'load_avg': load_avg
            }
        except Exception as e:
            print(f"Ошибка при получении информации о CPU: {e}")
            return {}
    
    def get_memory_info(self):
        """Получает информацию о памяти"""
        try:
            # Виртуальная память (RAM)
            virtual_memory = psutil.virtual_memory()
            
            # Swap память
            swap_memory = psutil.swap_memory()
            
            return {
                'memory_total': virtual_memory.total,
                'memory_available': virtual_memory.available,
                'memory_used': virtual_memory.used,
                'memory_free': virtual_memory.free,
                'memory_percent': virtual_memory.percent,
                'swap_total': swap_memory.total,
                'swap_used': swap_memory.used,
                'swap_free': swap_memory.free,
                'swap_percent': swap_memory.percent
            }
        except Exception as e:
            print(f"Ошибка при получении информации о памяти: {e}")
            return {}
    
    def get_disk_info(self):
        """Получает информацию о дисках"""
        try:
            disks = []
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'file_system': partition.fstype,
                        'total': partition_usage.total,
                        'used': partition_usage.used,
                        'free': partition_usage.free,
                        'percent': (partition_usage.used / partition_usage.total) * 100
                    }
                    disks.append(disk_info)
                except PermissionError:
                    # Некоторые разделы могут быть недоступны
                    continue
            
            # I/O статистика диска
            disk_io = psutil.disk_io_counters()
            io_info = None
            if disk_io:
                io_info = {
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_time': disk_io.read_time,
                    'write_time': disk_io.write_time
                }
            
            return {
                'disks': disks,
                'disk_io': io_info
            }
        except Exception as e:
            print(f"Ошибка при получении информации о дисках: {e}")
            return {}
    
    def get_network_info(self):
        """Получает информацию о сети"""
        try:
            # Сетевые интерфейсы
            network_interfaces = []
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, addresses in net_if_addrs.items():
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'is_up': net_if_stats[interface_name].isup if interface_name in net_if_stats else False
                }
                
                for addr in addresses:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                
                network_interfaces.append(interface_info)
            
            # I/O статистика сети
            net_io = psutil.net_io_counters()
            io_info = None
            if net_io:
                io_info = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
            
            return {
                'interfaces': network_interfaces,
                'network_io': io_info
            }
        except Exception as e:
            print(f"Ошибка при получении информации о сети: {e}")
            return {}
    
    def get_process_info(self, limit=10):
        """Получает информацию о процессах"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Сортируем по использованию CPU
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return {
                'total_processes': len(processes),
                'top_processes': processes[:limit]
            }
        except Exception as e:
            print(f"Ошибка при получении информации о процессах: {e}")
            return {}
    
    def collect_system_snapshot(self):
        """Собирает полный снимок системы"""
        timestamp = datetime.now().isoformat()
        
        snapshot = {
            'timestamp': timestamp,
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'processes': self.get_process_info()
        }
        
        return snapshot
    
    def check_thresholds(self, snapshot):
        """Проверяет пороговые значения и создает уведомления"""
        alerts = []
        timestamp = snapshot['timestamp']
        
        # Проверка CPU
        cpu_percent = snapshot['cpu'].get('cpu_percent', 0)
        if cpu_percent > self.thresholds['cpu_percent']:
            alerts.append({
                'timestamp': timestamp,
                'type': 'cpu_high',
                'message': f"Высокая загрузка CPU: {cpu_percent:.1f}%",
                'value': cpu_percent,
                'threshold': self.thresholds['cpu_percent']
            })
        
        # Проверка памяти
        memory_percent = snapshot['memory'].get('memory_percent', 0)
        if memory_percent > self.thresholds['memory_percent']:
            alerts.append({
                'timestamp': timestamp,
                'type': 'memory_high',
                'message': f"Высокое использование памяти: {memory_percent:.1f}%",
                'value': memory_percent,
                'threshold': self.thresholds['memory_percent']
            })
        
        # Проверка дисков
        for disk in snapshot['disk'].get('disks', []):
            if disk['percent'] > self.thresholds['disk_percent']:
                alerts.append({
                    'timestamp': timestamp,
                    'type': 'disk_high',
                    'message': f"Диск {disk['device']} заполнен на {disk['percent']:.1f}%",
                    'value': disk['percent'],
                    'threshold': self.thresholds['disk_percent']
                })
        
        return alerts
    
    def start_monitoring(self, interval=60):
        """Запускает мониторинг системы"""
        def monitor_loop():
            while self.monitoring:
                try:
                    snapshot = self.collect_system_snapshot()
                    self.log_data.append(snapshot)
                    
                    # Проверяем пороговые значения
                    new_alerts = self.check_thresholds(snapshot)
                    self.alerts.extend(new_alerts)
                    
                    # Ограничиваем количество алертов
                    if len(self.alerts) > 100:
                        self.alerts = self.alerts[-100:]
                    
                    # Периодически сохраняем данные
                    if len(self.log_data) % 10 == 0:
                        self.save_log_data()
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"Ошибка в цикле мониторинга: {e}")
                    time.sleep(interval)
        
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            self.monitor_thread.start()
            print(f"✅ Мониторинг запущен (интервал: {interval} сек)")
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        if self.monitoring:
            self.monitoring = False
            self.save_log_data()
            print("⏹️ Мониторинг остановлен")
    
    def get_statistics(self, hours=24):
        """Получает статистику за указанный период"""
        if not self.log_data:
            return None
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            entry for entry in self.log_data
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]
        
        if not recent_data:
            return None
        
        # Вычисляем средние значения
        cpu_values = [entry['cpu'].get('cpu_percent', 0) for entry in recent_data if entry['cpu'].get('cpu_percent')]
        memory_values = [entry['memory'].get('memory_percent', 0) for entry in recent_data if entry['memory'].get('memory_percent')]
        
        stats = {
            'period_hours': hours,
            'data_points': len(recent_data),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            }
        }
        
        return stats
    
    def display_current_status(self):
        """Отображает текущий статус системы"""
        snapshot = self.collect_system_snapshot()
        
        print("🖥️  ТЕКУЩИЙ СТАТУС СИСТЕМЫ")
        print("=" * 50)
        
        # CPU
        cpu = snapshot['cpu']
        print(f"\n🔥 ПРОЦЕССОР:")
        print(f"  📊 Загрузка: {cpu.get('cpu_percent', 0):.1f}%")
        if cpu.get('cpu_freq_current'):
            print(f"  ⚡ Частота: {cpu['cpu_freq_current']:.0f} MHz")
        
        # Память
        memory = snapshot['memory']
        memory_total_gb = memory.get('memory_total', 0) / (1024**3)
        memory_used_gb = memory.get('memory_used', 0) / (1024**3)
        print(f"\n💾 ПАМЯТЬ:")
        print(f"  📊 Использовано: {memory.get('memory_percent', 0):.1f}%")
        print(f"  💽 Объем: {memory_used_gb:.1f} GB / {memory_total_gb:.1f} GB")
        
        # Диски
        disk = snapshot['disk']
        print(f"\n💿 ДИСКИ:")
        for disk_info in disk.get('disks', []):
            total_gb = disk_info['total'] / (1024**3)
            used_gb = disk_info['used'] / (1024**3)
            print(f"  {disk_info['device']}: {disk_info['percent']:.1f}% ({used_gb:.1f}/{total_gb:.1f} GB)")
        
        # Топ процессов
        processes = snapshot['processes']
        print(f"\n⚙️  ТОП ПРОЦЕССОВ по CPU:")
        for proc in processes.get('top_processes', [])[:5]:
            print(f"  {proc['name'][:20]:20} {proc['cpu_percent'] or 0:6.1f}% CPU {proc['memory_percent'] or 0:6.1f}% RAM")
        
        return snapshot

def main():
    monitor = SystemMonitor()
    
    print("=== СИСТЕМНЫЙ МОНИТОР ===\n")
    
    while True:
        print("1. Показать текущий статус")
        print("2. Системная информация")
        print("3. Запустить мониторинг")
        print("4. Остановить мониторинг")
        print("5. Показать уведомления")
        print("6. Статистика")
        print("7. Настроить пороговые значения")
        print("8. Выход")
        
        choice = input("\nВыберите действие (1-8): ")
        
        if choice == "1":
            monitor.display_current_status()
            
        elif choice == "2":
            system_info = monitor.get_system_info()
            print("\n💻 СИСТЕМНАЯ ИНФОРМАЦИЯ")
            print("=" * 50)
            print(f"Система: {system_info.get('system')} {system_info.get('release')}")
            print(f"Компьютер: {system_info.get('node')}")
            print(f"Архитектура: {system_info.get('machine')}")
            print(f"CPU ядер: {system_info.get('cpu_count')} физических, {system_info.get('cpu_count_logical')} логических")
            
            memory_gb = system_info.get('memory_total', 0) / (1024**3)
            print(f"Память: {memory_gb:.1f} GB")
            
            if system_info.get('boot_time'):
                boot_time = datetime.fromtimestamp(system_info['boot_time'])
                uptime = datetime.now() - boot_time
                print(f"Время загрузки: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Время работы: {uptime.days} дней, {uptime.seconds//3600} часов")
                
        elif choice == "3":
            if monitor.monitoring:
                print("⚠️ Мониторинг уже запущен")
            else:
                try:
                    interval = int(input("Интервал мониторинга в секундах (по умолчанию 60): ") or "60")
                    monitor.start_monitoring(interval)
                except ValueError:
                    print("Используется интервал по умолчанию: 60 секунд")
                    monitor.start_monitoring()
                    
        elif choice == "4":
            monitor.stop_monitoring()
            
        elif choice == "5":
            print(f"\n🚨 УВЕДОМЛЕНИЯ ({len(monitor.alerts)})")
            print("=" * 50)
            
            if monitor.alerts:
                for alert in monitor.alerts[-20:]:  # Последние 20
                    timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
                    print(f"[{timestamp}] {alert['message']}")
            else:
                print("Уведомлений нет")
                
        elif choice == "6":
            try:
                hours = int(input("Статистика за сколько часов? (по умолчанию 24): ") or "24")
                stats = monitor.get_statistics(hours)
                
                if stats:
                    print(f"\n📈 СТАТИСТИКА за {hours} часов")
                    print("=" * 50)
                    print(f"Точек данных: {stats['data_points']}")
                    print(f"\nCPU:")
                    print(f"  Среднее: {stats['cpu']['avg']:.1f}%")
                    print(f"  Максимум: {stats['cpu']['max']:.1f}%")
                    print(f"  Минимум: {stats['cpu']['min']:.1f}%")
                    print(f"\nПамять:")
                    print(f"  Среднее: {stats['memory']['avg']:.1f}%")
                    print(f"  Максимум: {stats['memory']['max']:.1f}%")
                    print(f"  Минимум: {stats['memory']['min']:.1f}%")
                else:
                    print("❌ Недостаточно данных для статистики")
                    
            except ValueError:
                print("❌ Введите корректное число")
                
        elif choice == "7":
            print(f"\n⚙️  ПОРОГОВЫЕ ЗНАЧЕНИЯ")
            print(f"Текущие значения:")
            print(f"1. CPU: {monitor.thresholds['cpu_percent']}%")
            print(f"2. Память: {monitor.thresholds['memory_percent']}%")
            print(f"3. Диск: {monitor.thresholds['disk_percent']}%")
            
            try:
                setting_choice = input("\nИзменить какой параметр? (1-3 или Enter для пропуска): ")
                
                if setting_choice == "1":
                    new_value = float(input(f"Новое значение для CPU (текущее {monitor.thresholds['cpu_percent']}%): "))
                    monitor.thresholds['cpu_percent'] = new_value
                    print(f"✅ Порог CPU установлен: {new_value}%")
                    
                elif setting_choice == "2":
                    new_value = float(input(f"Новое значение для памяти (текущее {monitor.thresholds['memory_percent']}%): "))
                    monitor.thresholds['memory_percent'] = new_value
                    print(f"✅ Порог памяти установлен: {new_value}%")
                    
                elif setting_choice == "3":
                    new_value = float(input(f"Новое значение для диска (текущее {monitor.thresholds['disk_percent']}%): "))
                    monitor.thresholds['disk_percent'] = new_value
                    print(f"✅ Порог диска установлен: {new_value}%")
                    
            except ValueError:
                print("❌ Введите корректное числовое значение")
                
        elif choice == "8":
            monitor.stop_monitoring()
            print("До свидания! 🖥️")
            break
            
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
