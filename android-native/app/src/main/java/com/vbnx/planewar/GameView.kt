package com.vbnx.planewar

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Shader
import android.view.MotionEvent
import android.view.SurfaceHolder
import android.view.SurfaceView
import com.vbnx.planewar.game.Bullet
import com.vbnx.planewar.game.Enemy
import com.vbnx.planewar.game.EnemyType
import com.vbnx.planewar.game.Explosion
import com.vbnx.planewar.game.Player
import com.vbnx.planewar.game.StarField
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * 游戏主视图：SurfaceView + 自绘 Canvas 游戏循环
 *
 * 玩法：
 *  - 按住屏幕拖动，战机跟随手指（战机在手指上方，避免遮挡）
 *  - 自动开火；得分超过 300 解锁双发子弹
 *  - 小型敌机 1 血 / 中型 3 血 / 大型 6 血且会反击
 *  - 被撞击或中弹损失 1 条命，3 条命用完游戏结束，点击重开
 */
class GameView(context: Context) : SurfaceView(context), SurfaceHolder.Callback {

    enum class State { READY, RUNNING, GAME_OVER }

    @Volatile private var state = State.READY
    @Volatile private var running = false
    private var gameThread: Thread? = null

    private var screenW = 0f
    private var screenH = 0f

    // ---- 游戏对象 ----
    private val player = Player()
    private val enemies = ArrayList<Enemy>()
    private val playerBullets = ArrayList<Bullet>()
    private val enemyBullets = ArrayList<Bullet>()
    private val explosions = ArrayList<Explosion>()
    private var starField: StarField? = null

    // ---- 游戏数据 ----
    private var score = 0
    private var bestScore = 0
    private var lives = 3
    private var elapsed = 0f
    private var spawnTimer = 0f
    private var fireTimer = 0f

    @Volatile private var touchX = -1f
    @Volatile private var touchY = -1f

    // ---- 画笔 ----
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val hudPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 44f
        isFakeBoldText = true
    }
    private val centerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 72f
        textAlign = Paint.Align.CENTER
        isFakeBoldText = true
    }
    private val subPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#B0BEC5")
        textSize = 40f
        textAlign = Paint.Align.CENTER
    }

    private val prefs = context.getSharedPreferences("plane_war", Context.MODE_PRIVATE)

    init {
        holder.addCallback(this)
        isFocusable = true
        bestScore = prefs.getInt("best", 0)
    }

    // ---------- Surface 生命周期 ----------

    override fun surfaceCreated(holder: SurfaceHolder) {
        startLoop()
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        screenW = width.toFloat()
        screenH = height.toFloat()
        starField = StarField(screenW, screenH)
        if (!player.alive || player.x == 0f) {
            player.x = screenW / 2
            player.y = screenH * 0.8f
        }
    }

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        stopLoop()
    }

    fun pause() = stopLoop()

    fun resume() {
        if (holder.surface != null && holder.surface.isValid) startLoop()
    }

    private fun startLoop() {
        if (running) return
        running = true
        gameThread = Thread {
            var last = System.nanoTime()
            while (running) {
                val now = System.nanoTime()
                var dt = (now - last) / 1_000_000_000f
                last = now
                if (dt > 0.05f) dt = 0.05f

                tick(dt)

                val canvas = holder.lockCanvas() ?: continue
                try {
                    synchronized(holder) { render(canvas) }
                } finally {
                    holder.unlockCanvasAndPost(canvas)
                }
            }
        }.also { it.start() }
    }

    private fun stopLoop() {
        running = false
        gameThread?.join(500)
        gameThread = null
    }

    // ---------- 输入 ----------

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                when (state) {
                    State.READY -> state = State.RUNNING
                    State.GAME_OVER -> reset()
                    State.RUNNING -> {
                        touchX = event.x
                        touchY = event.y
                    }
                }
            }
            MotionEvent.ACTION_MOVE -> {
                touchX = event.x
                touchY = event.y
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                touchX = -1f
                touchY = -1f
            }
        }
        return true
    }

    // ---------- 逻辑 ----------

    private fun tick(dt: Float) {
        starField?.update(dt)

        // 爆炸粒子始终更新（游戏结束也能看到）
        val ei = explosions.iterator()
        while (ei.hasNext()) {
            val e = ei.next()
            e.update(dt)
            if (e.isFinished) ei.remove()
        }

        if (state != State.RUNNING) return

        elapsed += dt

        // 玩家跟随手指（战机显示在手指上方一段距离）
        if (touchX >= 0f) {
            val targetY = (touchY - 180f).coerceIn(player.radius, screenH - player.radius)
            player.x = touchX.coerceIn(player.radius, screenW - player.radius)
            player.y = targetY
        }

        spawnEnemies(dt)
        firePlayerBullets(dt)
        updateEnemies(dt)
        updateBullets(dt)
        handleCollisions()
    }

    private fun spawnEnemies(dt: Float) {
        val level = 1 + score / 400
        val interval = (1.05f - level * 0.07f).coerceAtLeast(0.3f)
        spawnTimer -= dt
        if (spawnTimer > 0f) return
        spawnTimer = interval

        val roll = Random.nextFloat()
        val type = when {
            level >= 3 && roll < 0.10f + level * 0.01f -> EnemyType.LARGE
            roll < 0.30f + level * 0.02f -> EnemyType.MEDIUM
            else -> EnemyType.SMALL
        }
        val margin = type.radius + 10f
        enemies.add(
            Enemy(
                type = type,
                x = margin + Random.nextFloat() * (screenW - margin * 2),
                y = -type.radius,
                screenWidth = screenW
            )
        )
    }

    private fun firePlayerBullets(dt: Float) {
        fireTimer -= dt
        if (fireTimer > 0f) return
        fireTimer = 0.18f

        val speed = -1500f
        val noseY = player.y - player.radius * 1.2f
        if (score >= 300) {
            // 双发
            playerBullets.add(Bullet(player.x - 16f, noseY, 0f, speed, friendly = true))
            playerBullets.add(Bullet(player.x + 16f, noseY, 0f, speed, friendly = true))
        } else {
            playerBullets.add(Bullet(player.x, noseY, 0f, speed, friendly = true))
        }
    }

    private fun updateEnemies(dt: Float) {
        val it = enemies.iterator()
        while (it.hasNext()) {
            val e = it.next()
            e.update(dt)
            if (e.shouldFire(dt, screenH)) {
                // 朝玩家方向发射
                val dx = player.x - e.x
                val dy = player.y - e.y
                val angle = atan2(dy, dx)
                val speed = 520f
                enemyBullets.add(
                    Bullet(e.x, e.y + e.radius, cos(angle) * speed, sin(angle) * speed, friendly = false)
                )
            }
            if (e.isOffScreen(screenH)) it.remove()
        }
    }

    private fun updateBullets(dt: Float) {
        val pi = playerBullets.iterator()
        while (pi.hasNext()) {
            val b = pi.next()
            b.update(dt)
            if (b.isOffScreen(screenW, screenH)) pi.remove()
        }
        val ei = enemyBullets.iterator()
        while (ei.hasNext()) {
            val b = ei.next()
            b.update(dt)
            if (b.isOffScreen(screenW, screenH)) ei.remove()
        }
    }

    private fun handleCollisions() {
        // 玩家子弹 vs 敌机
        val bi = playerBullets.iterator()
        while (bi.hasNext()) {
            val b = bi.next()
            val ei = enemies.iterator()
            var consumed = false
            while (ei.hasNext()) {
                val e = ei.next()
                if (dist(b.x, b.y, e.x, e.y) < b.radius + e.radius * 0.85f) {
                    e.hp -= b.damage
                    consumed = true
                    if (e.hp <= 0) {
                        score += e.type.score
                        explosions.add(Explosion(e.x, e.y, Color.parseColor(e.type.color)))
                        ei.remove()
                    }
                    break
                }
            }
            if (consumed) bi.remove()
        }

        if (!player.isInvincible) {
            // 敌机撞玩家
            val hitByEnemy = enemies.any {
                dist(player.x, player.y, it.x, it.y) < player.radius * 0.8f + it.radius * 0.8f
            }
            // 敌机子弹打玩家
            val bulletIt = enemyBullets.iterator()
            var hitByBullet = false
            while (bulletIt.hasNext()) {
                val b = bulletIt.next()
                if (dist(player.x, player.y, b.x, b.y) < player.radius * 0.7f + b.radius) {
                    bulletIt.remove()
                    hitByBullet = true
                    break
                }
            }
            if (hitByEnemy || hitByBullet) onPlayerHit()
        }
    }

    private fun onPlayerHit() {
        lives--
        explosions.add(Explosion(player.x, player.y, Color.parseColor("#4FC3F7")))
        if (lives <= 0) {
            state = State.GAME_OVER
            player.alive = false
            if (score > bestScore) {
                bestScore = score
                prefs.edit().putInt("best", bestScore).apply()
            }
        } else {
            player.invincibleUntil = System.currentTimeMillis() + 1500
            player.x = screenW / 2
            player.y = screenH * 0.8f
        }
    }

    private fun reset() {
        enemies.clear()
        playerBullets.clear()
        enemyBullets.clear()
        explosions.clear()
        score = 0
        lives = 3
        elapsed = 0f
        spawnTimer = 0f
        fireTimer = 0f
        player.alive = true
        player.invincibleUntil = 0L
        player.x = screenW / 2
        player.y = screenH * 0.8f
        state = State.RUNNING
    }

    private fun dist(x1: Float, y1: Float, x2: Float, y2: Float): Float {
        val dx = x1 - x2
        val dy = y1 - y2
        return sqrt(dx * dx + dy * dy)
    }

    // ---------- 绘制 ----------

    private fun render(canvas: Canvas) {
        // 深空渐变背景
        paint.shader = LinearGradient(
            0f, 0f, 0f, screenH,
            Color.parseColor("#050A1A"), Color.parseColor("#10254F"),
            Shader.TileMode.CLAMP
        )
        canvas.drawRect(0f, 0f, screenW, screenH, paint)
        paint.shader = null

        starField?.draw(canvas, paint)

        for (e in enemies) e.draw(canvas, paint)
        for (b in playerBullets) b.draw(canvas, paint)
        for (b in enemyBullets) b.draw(canvas, paint)
        player.draw(canvas, paint)
        for (e in explosions) e.draw(canvas, paint)

        drawHud(canvas)

        when (state) {
            State.READY -> {
                centerPaint.textSize = 84f
                canvas.drawText("飞机大战", screenW / 2, screenH * 0.38f, centerPaint)
                subPaint.textSize = 42f
                canvas.drawText("拖动手指移动战机，自动开火", screenW / 2, screenH * 0.5f, subPaint)
                canvas.drawText("点击屏幕开始", screenW / 2, screenH * 0.58f, subPaint)
            }
            State.GAME_OVER -> {
                centerPaint.textSize = 80f
                canvas.drawText("游戏结束", screenW / 2, screenH * 0.4f, centerPaint)
                subPaint.textSize = 46f
                canvas.drawText("得分：$score    最高：$bestScore", screenW / 2, screenH * 0.5f, subPaint)
                canvas.drawText("点击屏幕重新开始", screenW / 2, screenH * 0.58f, subPaint)
            }
            State.RUNNING -> Unit
        }
    }

    private fun drawHud(canvas: Canvas) {
        hudPaint.textAlign = Paint.Align.LEFT
        hudPaint.textSize = 44f
        canvas.drawText("得分 $score", 28f, 64f, hudPaint)
        hudPaint.textAlign = Paint.Align.RIGHT
        canvas.drawText("最高 $bestScore", screenW - 28f, 64f, hudPaint)

        // 生命（小飞机图标简化为爱心圆点）
        hudPaint.textAlign = Paint.Align.LEFT
        canvas.drawText("生命", 28f, 122f, hudPaint)
        paint.style = Paint.Style.FILL
        paint.color = Color.parseColor("#EF5350")
        for (i in 0 until lives) {
            canvas.drawCircle(140f + i * 44f, 108f, 14f, paint)
        }
    }
}
