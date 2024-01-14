import json
import threading
import time
from websocket import create_connection
import matplotlib.pyplot as plt

from config import SUBSCRIBE_MSG_CONFIG, WEB_SOCKET_URL

class OrderBookMonitor:
    def __init__(self, update_interval=1):
        self.update_interval = update_interval
        self.order_book = {'bids': {}, 'asks': {}}
        self.total_changes = {'bids': 0, 'asks': 0}
        self.lock = threading.Lock()
        self.timestamps = []
        self.buy_rate_of_speed = []
        self.sell_rate_of_speed = []
        self.total_speed = []

    def connect_to_websocket(self):
        url = WEB_SOCKET_URL
        print('Creating the connection')
        self.ws = create_connection(url)
        self.ws.send(json.dumps(SUBSCRIBE_MSG_CONFIG))
        print('Connection created')

    def disconnect_from_websocket(self):
        try:
            self.ws.close()
        except:
            pass

    def on_message(self, message):
        data = json.loads(message)
        if 'bids' in data or 'asks' in data:
            with self.lock:
                if 'bids' in data:                    
                    self.total_changes['bids'] += len(data['bids'])
                if 'asks' in data:                    
                    self.total_changes['asks'] += len(data['asks'])

    def listen_to_order_book(self):
        while True:
            message = self.ws.recv()
            self.on_message(message)
            time.sleep(self.update_interval)

    def start_monitoring(self):
        self.connect_to_websocket()
        threading.Thread(target=self.listen_to_order_book, daemon=True).start()

    def stop_monitoring(self):
        self.disconnect_from_websocket()

    def calculate_rate_of_change(self):
        with self.lock:
            try:
                total_time = self.timestamps[-1] - self.timestamps[0]
                buy_rate = self.total_changes['bids'] / total_time
                sell_rate = self.total_changes['asks'] / total_time
                self.buy_rate_of_speed.append(buy_rate)
                self.sell_rate_of_speed.append(sell_rate)
                self.total_speed.append(buy_rate+sell_rate)
            except Exception as e:
                pass

    def plot_rate_of_change(self):
        self.timestamps = self.timestamps[len(self.timestamps)-len(self.sell_rate_of_speed):]
        plt.plot(self.timestamps, self.buy_rate_of_speed, label='Buy Speed')
        plt.plot(self.timestamps, self.sell_rate_of_speed, label='Sell Speed')
        plt.plot(self.timestamps, self.total_speed, label='Total Speed')
        plt.xlabel('Time (minutes)')
        plt.ylabel('Change per seconds')
        plt.legend()
        plt.show()

    def run(self):
        while True:
            self.timestamps.append(time.time())
            self.calculate_rate_of_change()            
            time.sleep(self.update_interval)

if __name__ == "__main__":
    order_book_monitor = OrderBookMonitor(update_interval=1)
    order_book_monitor.start_monitoring()
    try:
        order_book_monitor.run()
    except KeyboardInterrupt:
        order_book_monitor.stop_monitoring()
        order_book_monitor.plot_rate_of_change()


