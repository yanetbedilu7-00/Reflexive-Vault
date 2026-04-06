import sqlite3
from datetime import datetime, timedelta

class TrustScoreEngine:
    def __init__(self):
        self.conn = sqlite3.connect('agent_behavior.db')
        self._init_db()
        self.trust_score = 100
        self.threshold = 70
    
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                scope_requested TEXT,
                confidence REAL,
                outcome TEXT
            )
        ''')
        self.conn.commit()
    
    def calculate_trust_score(self):
        cursor = self.conn.cursor()
        
        five_min_ago = datetime.now() - timedelta(minutes=5)
        cursor.execute('''
            SELECT COUNT(*) FROM agent_actions 
            WHERE timestamp > ? AND outcome = 'anomaly'
        ''', (five_min_ago,))
        anomalies = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM agent_actions 
            WHERE timestamp > ? 
        ''', (datetime.now() - timedelta(seconds=30),))
        recent_requests = cursor.fetchone()[0]
        
        score = 100
        score -= anomalies * 15
        if recent_requests > 20:
            score -= 30
        
        self.trust_score = max(0, min(100, score))
        return self.trust_score
    
    def log_action(self, action, scope, confidence, outcome="normal"):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO agent_actions (action, scope_requested, confidence, outcome)
            VALUES (?, ?, ?, ?)
        ''', (action, scope, confidence, outcome))
        self.conn.commit()
    
    def is_authorized(self, required_scope):
        current_score = self.calculate_trust_score()
        
        risk_levels = {
            "read:data": 30,
            "analyze:data": 50,
            "write:data": 70,
            "admin:override": 90,
            "share:output": 60
        }
        
        required_trust = risk_levels.get(required_scope, 80)
        
        if current_score < required_trust:
            raise PermissionError(
                f"Trust score {current_score} below required {required_trust} "
                f"for {required_scope}. Immune response triggered."
            )
        
        return True